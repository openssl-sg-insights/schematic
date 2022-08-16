from typing import Dict, List, Tuple, Union
from abc import ABC, abstractmethod
# all pre-requsite steps for generating manifest
# should provide general materials needed for constructing manifests regardless of formats
# this should serve as the "abstraction" layer

class RecordView(object):
    def __init__(self, path_to_json_ld, root, additional_metadata, use_annotations, order_valid_value, order_headers):
        self.path_to_json_ld = path_to_json_ld
        self.root = root
        self.use_annoatations = use_annotations 
        self.order_valid_value = order_valid_value
        self.additional_metadata = additional_metadata
        self.order_headers = order_headers

    def _get_json_schema(self, json_schema_filepath: str) -> Dict:
        # open json schema as a dictionary 
        # returning a dictionary containing portions of json schema 
        # the json schema depdents on the "root/component"
        pass
    
    def _get_required_metadata_fields(self, json_schema, fields) -> Dict:
        pass
        # return required_metadata_fields

    def _gather_dependency_requirements(self, json_schema, required_metadata_fields) -> Dict:
        pass
        # return required_metadata_fields

    def _get_additional_metadata(self, required_metadata_fields:dict) -> Dict:
         pass
         # return required_metadata_fields

    def _gather_all_fields(self, fields, json_schema) -> Dict:
        # the goal of this function is to gather all the attributes/fields to include as columns

        # call _get_required_metadata_fields
        # call _gather_dependency_requirements
        # call _get_additional_metadata_

        # return required_metadata_fields
        pass
    
    def _mark_required_columns(self, required_metadata_fields, json_schema) -> Dict:
        # see _request_notes_comments in the old design 

        # the goal of this function is to find out all the required columns (so that we could set their background to pale blue in later step)


        pass 

    def _sort_manifest_fields(self, manifest_fields, order_headers="schema") -> List:
        # order manifest fields alphabetically 

        # order manifest fields based on data model schema 

        # this should return a sorted manifest field

        pass
    
    def _mark_column_order(self, sorted_manifest_field) -> Dict: 
        # this should return a dictionary marking the order of manifest column 

        # something like: {"familyHistory": {"column_order": 1}}
        pass

    def _get_column_header_note(self, required_metadata_fields) -> Dict:
        # see _request_row_format function in the old design

        # this function should return something like: 
        # {"familyHistory":{"note":[]}}

        pass
    
    def construct_record_requirements(self, attribute) -> Dict: 
        # this operation is for constructing a single record

        # this should return something like this for a single record: 
        # {"component": "MockComponent", "attribute": "FamilyHistory", "valid value": [], "required": true, "note": ""}

        # if attribute is a list with more than one items: 
        # {"component": "MockComponent", "attribute": {"FamilyHistory":{"valid value": [], "required": true, "note":"", "order": 1}, "CancerType": {"valid value": [], "required": true, "note":"", "order": 2}}}

        pass

    def construct_form_requirements(self) -> Dict:
        # gather all the fields and their valid values
        # call _gather_all_field

        # mark some of the columns as "required"
        # call _mark_required_columns function

        # sort manifest fields
        # call _mark_column_order function to mark the order of columns

        # get note of column headers
        # add note to column headers (if there's any)

        # this should return a dictionary like this: 
        # {"component": "MockComponent", "attributes": {"FamilyHistory":{"valid value": [], "required": true, "note":"", "order": 1}, "CancerType": {"valid value": [], "required": true, "note":"", "order": 2}}}
        pass

    
# the implementation interface
# here we listed all the formatting needed for manifest/record
class ViewImplmentation(ABC):
    @abstractmethod
    def implement_column_data_validation_values(self):
        pass
    
    @abstractmethod
    def order_column(self):
        pass
    
    @abstractmethod
    def add_note_to_header(self):
        pass

    @abstractmethod
    def create_drop_down_multi_select(self):
        pass
    
    @abstractmethod
    def implement_dependency_formatting(self):
        pass

    @abstractmethod
    def distinguish_required_columns(self):
        pass
    
    @abstractmethod
    def create_empty_interface(self):
        pass
    
    @abstractmethod
    def populate_existing_interface(self):
        pass
    
    @abstractmethod
    def get_interface_with_annotations(self):
        pass

class RecordGenerator(ViewImplmentation):
    def __init__(self, RecordView, title="Example", attribute=""):
        self.RecordView = RecordView
        self.required_info_attribute = self.RecordView.construct_record_requirements()
        self.ordered_metadata_fields = self.order_column() # get ordered column as a list 
        self.title = title
        self.attribute = attribute

    def implement_column_data_validation_values(self):
        pass
    
    def order_column(self):
        pass
    
    def add_note_to_header(self):
        pass

    def create_drop_down_multi_select(self):
        pass
    
    def implement_dependency_formatting(self):
        pass

    def distinguish_required_columns(self):
        pass
    
    def create_empty_interface(self):
        pass
    
    def populate_existing_interface(self):
        pass
    
    def get_interface_with_annotations(self):
        pass



class GoogleSheetGenerator(ViewImplmentation):
    def __init__(self, RecordView, title="Example", oauth=True):
        self.RecordView = RecordView
        self.required_info_form = self.RecordView.construct_form_requirements()
        self.spreadsheet_id = self._request_spreadsheet_id() # get spreadsheet id
        self.ordered_metadata_fields = self.order_column() # get ordered column as a list 
        self.title = title
        self.oauth = oauth # related to google sheet service credentials


    def _request_spreadsheet_id(self) -> str: 
        # get a spreadsheet id 
        # see _create_empty_manifest_spreadsheet in the old design 
        pass

    def _set_permissions(self): 
        pass

    def implement_column_data_validation_values(self):
        # apply validation rules 
        # see "_get_column_data_validation_values" in the old design
        pass

    def order_column(self): 
        pass
    
    def _regex_match_vr_formatting(self): 
        pass

    def add_note_to_header(self):
        pass

    def _request_note_multi_select(self):
        pass

    def distinguish_required_columns():
        pass

    def _request_cell_borders():
        pass

    def create_drop_down_multi_select(): 
        pass

    def implement_dependency_formatting(): 
        pass

    def _create_requests_body(self, required_info_form, spreadsheet_id) -> Dict:
        request_body = {}
        request_body["requests"] = []

        # set permission 
        # cal _set_permissions

        # construct regex formatting 
        # call _request_regex_match_vr_formatting

        # add notes to headers to provide more descriptions
        # call _request_notes_headers

        # add notes to multi-select
        # call _request_note_multi_select

        # request color changes based on if the columns are required or not
        # call _request_color_required_columns

        # adding value constraints

        # request dropdown or multi-select 
        # call _request_dropdown_or_multi 

        # set border formatting 
        # call _request_cell_borders

        # generate conditional formatting 
        # call _request_dependency_formatting
        pass

    def create_drop_down_multi_select(self):
        # execute_google_api_requests(
        #     self.sheet_service,
        #     requests_body,
        #     service_type="batch_update",
        #     spreadsheet_id=spreadsheet_id,
        # )

        # return manifest_url 
        pass 

    def set_dataframe_by_url(self):
        # Update Google Sheets using given pandas DataFrame.
        pass
    
    def get_dataframe_by_url(self):
        # Retrieve pandas DataFrame from table in Google Sheets
        pass
    
    def get_interface_with_annotations(self):
        pass

    def get_manifest(self):
        # Gets manifest for a given dataset on Synapse.
        pass

    def create_empty_interface(self):
        pass

    def populate_existing_interface(self):
        # populate a google sheet based on an existing manifest
        pass

class RTableGenerator(ViewImplmentation):
    def implement_column_data_validation_values(self):
        pass
    
    def order_column(self):
        pass
    
    def add_note_to_header(self):
        pass

    def create_drop_down_multi_select(self):
        pass
    
    def implement_dependency_formatting(self):
        pass

    def distinguish_required_columns(self):
        pass
    
    def create_empty_interface(self):
        pass
    
    def populate_existing_interface(self):
        pass
    
    def get_interface_with_annotations(self):
        pass

    def get_dataframe_by_table(self):
        # Retrieve pandas DataFrame from Rtable
        pass
    def _create_request_body(): 
        pass




#### Mock implementation 
path_to_json_ld = ''
title = 'example'
root = ''
use_annotations = ''
order_valid_value = ''
order_headers = ''
additional_metadata = {}
oauth=True

# start generating manifest
rv = RecordView(path_to_json_ld,root, use_annotations, additional_metadata, order_valid_value, order_headers)
gs = GoogleSheetGenerator(rv, title=title, oauth=oauth)

# create an empty google sheet
gs.create_empty_interface()