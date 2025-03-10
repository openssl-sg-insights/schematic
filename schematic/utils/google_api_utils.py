import os
import pickle
import logging

import pygsheets as ps

from typing import Dict, Any

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2 import service_account
from google.oauth2.credentials import Credentials
from schematic import CONFIG
from schematic.store.synapse import SynapseStorage
import pandas as pd

logger = logging.getLogger(__name__)


# If modifying these scopes, delete the file token.pickle.
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


# it will create 'token.pickle' based on credentials.json
def generate_token() -> Credentials:
    creds = None
    # The file token.pickle stores the user's access and refresh tokens,
    # and is created automatically when the authorization flow completes for the first time.
    if os.path.exists(CONFIG.TOKEN_PICKLE):
        with open(CONFIG.TOKEN_PICKLE, "rb") as token:
            creds = pickle.load(token)

    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CONFIG.CREDS_PATH, SCOPES)
            creds = flow.run_console()  ### don't have to deal with ports
        # Save the credentials for the next run
        with open(CONFIG.TOKEN_PICKLE, "wb") as token:
            pickle.dump(creds, token)

    return creds


# TODO: replace by pygsheets calls?
def build_credentials() -> Dict[str, Any]:
    creds = generate_token()

    # get a Google Sheet API service
    sheet_service = build("sheets", "v4", credentials=creds)
    # get a Google Drive API service
    drive_service = build("drive", "v3", credentials=creds)

    return {
        "sheet_service": sheet_service,
        "drive_service": drive_service,
        "creds": creds,
    }


def build_service_account_creds() -> Dict[str, Any]:
    credentials = service_account.Credentials.from_service_account_file(
        CONFIG.SERVICE_ACCT_CREDS, scopes=SCOPES
    )

    # get a Google Sheet API service
    sheet_service = build("sheets", "v4", credentials=credentials)
    # get a Google Drive API service
    drive_service = build("drive", "v3", credentials=credentials)

    return {
        "sheet_service": sheet_service,
        "drive_service": drive_service,
        "creds": credentials,
    }


def download_creds_file(auth: str = "token") -> None:
    if auth is None:
        raise ValueError(
            f"'{auth}' is not a valid authentication method. Please "
            "enter one of 'token' or 'service_account'."
        )

    syn = SynapseStorage.login()

    if auth == "token":
        if not os.path.exists(CONFIG.CREDS_PATH):
            # synapse ID of the 'credentials.json' file
            API_CREDS = CONFIG["synapse"]["token_creds"]

            # Download in parent directory of CREDS_PATH to
            # ensure same file system for os.rename()
            creds_dir = os.path.dirname(CONFIG.CREDS_PATH)

            creds_file = syn.get(API_CREDS, downloadLocation=creds_dir)
            os.rename(creds_file.path, CONFIG.CREDS_PATH)

            logger.info(
                "The credentials file has been downloaded " f"to '{CONFIG.CREDS_PATH}'"
            )

    elif auth == "service_account":
        if not os.path.exists(CONFIG.SERVICE_ACCT_CREDS):
            # synapse ID of the 'schematic_service_account_creds.json' file
            API_CREDS = CONFIG["synapse"]["service_acct_creds"]

            # Download in parent directory of SERVICE_ACCT_CREDS to
            # ensure same file system for os.rename()
            creds_dir = os.path.dirname(CONFIG.SERVICE_ACCT_CREDS)

            creds_file = syn.get(API_CREDS, downloadLocation=creds_dir)
            os.rename(creds_file.path, CONFIG.SERVICE_ACCT_CREDS)

            logger.info(
                "The credentials file has been downloaded "
                f"to '{CONFIG.SERVICE_ACCT_CREDS}'"
            )

    else:
        logger.warning(
            f"The mode of authentication you selected '{auth}' is "
            "not supported. Please use one of either 'token' or "
            "'service_account'."
        )


def execute_google_api_requests(service, requests_body, **kwargs):
    """
    Execute google API requests batch; attempt to execute in parallel.
    Args:
        service: google api service; for now assume google sheets service that is instantiated and authorized
        service_type: default batchUpdate; TODO: add logic for values update
        kwargs: google API service parameters
    Return: google API response
    """

    if (
        "spreadsheet_id" in kwargs
        and "service_type" in kwargs
        and kwargs["service_type"] == "batch_update"
    ):
        # execute all requests
        response = (
            service.spreadsheets()
            .batchUpdate(spreadsheetId=kwargs["spreadsheet_id"], body=requests_body)
            .execute()
        )

        return response

def export_manifest_csv(file_name, manifest):

    # intialize drive service 
    services_creds = build_service_account_creds()
    drive_service = services_creds["drive_service"]

    if isinstance(manifest, pd.DataFrame):
        manifest.to_csv(file_name, index=False)
    else: 
        # get spreadsheet id from url 
        spreadsheet_id = manifest.split('/')[-1]

        # use google drive
        # if successful, this method returns the file content as bytes
        data = drive_service.files().export(fileId=spreadsheet_id, mimeType='text/csv').execute()

        # open file and write data
        with open(file_name, 'wb') as f:
            f.write(data)
        f.close
    
def export_manifest_excel(manifest, output_excel=None):
    # intialize drive service 
    services_creds = build_service_account_creds()
    sheet_service = services_creds["sheet_service"]

    if isinstance(manifest, pd.DataFrame):
        manifest.to_excel(output_excel, index=False)
    else:
        # get spreadsheet id from url 
        spreadsheet_id = manifest.split('/')[-1]

        # use google sheet api
        sheet_metadata = sheet_service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
        sheets = sheet_metadata.get('sheets')

        # export to Excel
        writer = pd.ExcelWriter(output_excel)

        # export each sheet in manifest
        for sheet in sheets:
            dataset = sheet_service.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range=sheet['properties']['title']).execute()
            dataset_df = pd.DataFrame(dataset['values'])
            dataset_df.columns = dataset_df.iloc[0]
            dataset_df.drop(dataset_df.index[0], inplace=True)
            dataset_df.to_excel(writer, sheet_name=sheet['properties']['title'], index=False)
        writer.save()
        writer.close()   