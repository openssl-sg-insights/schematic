import builtins
from jsonschema import ValidationError
import logging

import numpy as np
import pandas as pd
import re
import sys
from os import getenv

# allows specifying explicit variable types
from typing import Any, Dict, Optional, Text, List
from urllib.parse import urlparse
from urllib.request import urlopen, OpenerDirector, HTTPDefaultErrorHandler
from urllib.request import Request
from urllib import error

from schematic.store.synapse import SynapseStorage
from schematic.store.base import BaseStorage
from schematic.schemas.generator import SchemaGenerator
from schematic.utils.validate_utils import comma_separated_list_regex
import time

from schematic.utils.validate_utils import parse_str_series_to_list

logger = logging.getLogger(__name__)

class GenerateError:
    def generate_schema_error(row_num: str, attribute_name: str, error_msg: str)-> List[str]:
        '''
        Purpose: Process error messages generated from schema
        Input:
            - row_num: the row the error occurred on.
            - attribute_name: the attribute the error occurred on.
            - error_msg: Error message
        '''
        error_col = attribute_name  # Attribute name
        error_row = row_num  # index row of the manifest where the error presented.
        error_message = error_msg

        arg_error_string = (
                f"For the attribute '{error_col}', on row {error_row}, {error_message}."
        )
        logging.error(arg_error_string)
        return [error_row, error_col, error_message]

    def generate_list_error(
        list_string: str, row_num: str, attribute_name: str, list_error: str,
        invalid_entry:str,
    ) -> List[str]:
        """
            Purpose:
                If an error is found in the string formatting, detect and record
                an error message.
            Input:
                - list_string: the user input list, that is represented as a string.
                - row_num: the row the error occurred on.
                - attribute_name: the attribute the error occurred on.
            Returns:
                Logging.error.
                Errors: List[str] Error details for further storage.
            """
        if list_error == "not_comma_delimited":
            error_str = (
                f"For attribute {attribute_name} in row {row_num} it does not "
                f"appear as if you provided a comma delimited string. Please check "
                f"your entry ('{list_string}'') and try again."
            )
            logging.error(error_str)
            error_row = row_num  # index row of the manifest where the error presented.
            error_col = attribute_name  # Attribute name
            error_message = error_str
            error_val = invalid_entry
        return [error_row, error_col, error_message, error_val]

    def generate_regex_error(
        val_rule: str,
        reg_expression: str,
        row_num: str,
        module_to_call: str,
        attribute_name: str,
        invalid_entry:str,
    ) -> List[str]:
        """
            Purpose:
                Generate an logging error as well as a stored error message, when
                a regex error is encountered.
            Input:
                val_rule: str, defined in the schema.
                reg_expression: str, defined in the schema
                row_num: str, row where the error was detected
                module_to_call: re module specified in the schema
                attribute_name: str, attribute being validated
            Returns:
                Logging.error.
                Errors: List[str] Error details for further storage.
            """
        regex_error_string = (
            f"For the attribute {attribute_name}, on row {row_num}, the string is not properly formatted. "
            f'It should follow the following re.{module_to_call} pattern "{reg_expression}".'
        )
        logging.error(regex_error_string)
        error_row = row_num  # index row of the manifest where the error presented.
        error_col = attribute_name  # Attribute name
        error_message = regex_error_string
        error_val = invalid_entry
        return [error_row, error_col, error_message, error_val]

    def generate_type_error(
        val_rule: str, row_num: str, attribute_name: str, invalid_entry:str,
    ) -> List[str]:
        """
            Purpose:
                Generate an logging error as well as a stored error message, when
                a type error is encountered.
            Input:
                val_rule: str, defined in the schema.
                row_num: str, row where the error was detected
                attribute_name: str, attribute being validated
            Returns:
                Logging.error.
                Errors: List[str] Error details for further storage.
            """
        type_error_str = (
            f"On row {row_num} the attribute {attribute_name} "
            f"does not contain the proper value type {val_rule}."
        )
        logging.error(type_error_str)
        error_row = row_num  # index row of the manifest where the error presented.
        error_col = attribute_name  # Attribute name
        error_message = type_error_str
        error_val = invalid_entry
        return [error_row, error_col, error_message, error_val]

    def generate_url_error(
        url: str, url_error: str, row_num: str, attribute_name: str, argument: str,
        invalid_entry:str,
    ) -> List[str]:
        """
            Purpose:
                Generate an logging error as well as a stored error message, when
                a URL error is encountered.

                Types of errors included:
                    - Invalid URL: Refers to a URL that brings up an error when 
                        attempted to be accessed such as a HTTPError 404 Webpage Not Found.
                    - Argument Error: this refers to a valid URL that does not 
                        contain within it the arguments specified by the schema,
                        such as 'protocols.io' or 'dox.doi.org'
                    - Random Entry: this refers to an entry try that is not 
                        validated to be a URL.
                        e.g. 'lkejrlei', '0', 'not applicable'
            Input:
                url: str, that was input by the user.
                url_error: str, error detected in url_validation()
                attribute_name: str, attribute being validated
                argument: str, argument being validated.
            Returns:
                Logging.error.
                Errors: List[str] Error details for further storage.
            """
        error_row = row_num  # index row of the manifest where the error presented.
        error_col = attribute_name  # Attribute name
        if url_error == "invalid_url":
            invalid_url_error_string = (
                f"For the attribute '{attribute_name}', on row {row_num}, the URL provided ({url}) does not "
                f"conform to the standards of a URL. Please make sure you are entering a real, working URL "
                f"as required by the Schema."
            )
            logging.error(invalid_url_error_string)
            error_message = invalid_url_error_string
            error_val = invalid_entry
        elif url_error == "arg_error":
            arg_error_string = (
                f"For the attribute '{attribute_name}', on row {row_num}, the URL provided ({url}) does not "
                f"conform to the schema specifications and does not contain the required element: {argument}."
            )
            logging.error(arg_error_string)
            error_message = arg_error_string
            error_val = f"URL Error: Argument Error"
        elif url_error == "random_entry":
            random_entry_error_str = (
                f"For the attribute '{attribute_name}', on row {row_num}, the input provided ('{url}'') does not "
                f"look like a URL, please check input and try again."
            )
            logging.error(random_entry_error_str)
            error_message = random_entry_error_str
            error_val = f"URL Error: Random Entry"
        return [error_row, error_col, error_message, error_val]

    def generate_cross_warning(
        val_rule: str,
        attribute_name: str,
        matching_manifests = [],
        missing_manifest_ID = None,
        invalid_entry = None,
        row_num = None,
    ) -> List[str]:
        """
            Purpose:
                Generate an logging error as well as a stored error message, when
                a cross validation error is encountered.
            Input:
                val_rule: str, defined in the schema.
                matching_manifests: list of manifests with all values in the target attribute present
                manifest_ID: str, synID of the target manifest missing the source value
                attribute_name: str, attribute being validated
                invalid_entry: str, value present in source manifest that is missing in the target
                row_num: row in source manifest with value missing in target manifests             
            Returns:
                Logging.error.
                Errors: List[str] Error details for further storage.
            """
        
        if val_rule.__contains__('matchAtLeast'):
            cross_error_str = (
                f"Value(s) {invalid_entry} from row(s) {row_num} of the attribute {attribute_name} in the source manifest are missing." )
            cross_error_str += f" Manifest(s) {missing_manifest_ID} are missing the value(s)." if missing_manifest_ID else ""
            
        elif val_rule.__contains__('matchExactly'):
            if matching_manifests != []:
                cross_error_str = (
                    f"All values from attribute {attribute_name} in the source manifest are present in {len(matching_manifests)} manifests instead of only 1.")
                cross_error_str += f" Manifests {matching_manifests} match the values in the source attribute." if matching_manifests else ""
                    
            elif val_rule.__contains__('set'):
                cross_error_str = (
                    f"No matches for the values from attribute {attribute_name} in the source manifest are present in any other manifests instead of being present in exactly 1. "
                )
            elif val_rule.__contains__('value'):
                cross_error_str = (
                    f"Value(s) {invalid_entry} from row(s) {row_num} of the attribute {attribute_name} in the source manifest are not present in only one other manifest. " 
                )            

        logging.warning(cross_error_str)
        error_row = row_num  # index row of the manifest where the error presented.
        error_col = attribute_name  # Attribute name
        error_message = cross_error_str
        error_val = invalid_entry #Value from source manifest missing from targets
        
        return [error_row, error_col, error_message, error_val]

    def generate_content_error(
        val_rule: str,
        attribute_name: str,
        sg: SchemaGenerator,
        row_num = None,
        error_val = None,    
    ) -> (List[str], List[str]):
        """
        Purpose:
            Generate an logging error or warning as well as a stored error/warning message when validating the content of a manifest attribute.

            Types of error/warning included:
                - recommended - Raised when an attribute is empty and recommended but not required.
                - unique - Raised when attribute values are not unique.
                - protectAges - Raised when an attribute contains ages below 18YO or over 90YO that should be censored.
        Input:
                val_rule: str, defined in the schema.
                attribute_name: str, attribute being validated
                sg: schemaGenerator object
                row_num: str, row where the error was detected
                error_val: value duplicated

        Returns:
            Logging.error or Logging.warning.
            Message: List[str] Error|Warning details for further storage.
        """
        error_list = []
        warning_list = []
        error_col = attribute_name  # Attribute name
        
        #Determine whether to raise a warning or error
        raises = GenerateError.get_message_level(
            val_rule=val_rule,
            attribute_name = attribute_name,
            sg = sg,
            )

        #if a message needs to be raised, get the approrpiate function to do so
        if raises:
            logLevel = getattr(logging,raises)  
        else:
            return error_list, warning_list
        
        #log warning or error message
        if val_rule.startswith('recommended'):
            cross_error_str = (
                f"Column {attribute_name} is recommended but empty."
            )
            logLevel(cross_error_str)
            error_message = cross_error_str

            if raises == 'error':
                error_list = [error_col, error_message]
            #return warning and empty list for errors
            elif raises == 'warning':
                warning_list = [error_col, error_message]

            return error_list, warning_list

        elif val_rule.startswith('unique'):    
            cross_error_str = (
                f"Column {attribute_name} has the duplicate value(s) {set(error_val)} in rows: {row_num}."
            )

        elif val_rule.startswith('protectAges'):
            cross_error_str = (
                f"Column {attribute_name} contains ages that should be censored in rows: {row_num}."
            )           

        elif val_rule.startswith('inRange'):
            cross_error_str = (
                f"{attribute_name} values in rows {row_num} are out of the specified range."
            )  

        logLevel(cross_error_str)
        error_row = row_num 
        error_message = cross_error_str

        #return error and empty list for warnings
        if raises == 'error':
            error_list = [error_row, error_col, error_message, set(error_val)]
        #return warning and empty list for errors
        elif raises == 'warning':
            warning_list = [error_row, error_col, error_message, set(error_val)]
        
        return error_list, warning_list

    def get_message_level(
        val_rule: str,
        sg: SchemaGenerator,
        attribute_name: str,
        ) -> str:
        """
        Purpose:
            Determine whether an error or warning message should be logged and displayed

            Types of error/warning included:
                - recommended - Raised when an attribute is empty and recommended but not required.
                - unique - Raised when attribute values are not unique.
                - protectAges - Raised when an attribute contains ages below 18YO or over 90YO that should be censored.
        Input:
                val_rule: str, defined in the schema.
                sg: schemaGenerator object
                attribute_name: str, attribute being validated
        Returns:
            'error' or 'warning'
        """

        
        rule_parts = val_rule.split(" ")
        
        #See if the node is required, if it is and the column is missing then a requirement error will be raised later; no error or waring logged here if recommended and required but missing        
        if val_rule.startswith('recommended') and sg.is_node_required(node_display_name=attribute_name):
            level = None
        
        #if not required, use the message level specified in the rule
        elif rule_parts[-1].lower() == 'error':
            level = 'error'

        elif rule_parts[-1].lower() == 'warning':
            level = 'warning'
        
        #if no level specified, the default level is warning
        else:
            level = 'warning'

        return level

class ValidateAttribute(object):
    """
    A collection of functions to validate manifest attributes.
        list_validation
        regex_validation
        type_validation
        url_validation
        cross_validation
        get_target_manifests - helper function
    See functions for more details.
    TODO:
        - Add year validator
        - Add string length validator
    """

    def get_target_manifests(target_component, project_scope: List):

        target_manifest_IDs=[]
        target_dataset_IDs=[]
        
        #login
        access_token = getenv("SYNAPSE_ACCESS_TOKEN")
        if access_token:
            synStore = SynapseStorage(access_token=access_token,project_scope=project_scope)
        else:
            synStore = SynapseStorage(project_scope=project_scope)        

        #Get list of all projects user has access to
        projects = synStore.getStorageProjects(project_scope=project_scope)
        for project in projects:
            
            #get all manifests associated with datasets in the projects
            target_datasets=synStore.getProjectManifests(projectId=project[0])

            #If the manifest includes the target component, include synID in list
            for target_dataset in target_datasets:
                if target_component == target_dataset[-1][0].replace(" ","").lower() and target_dataset[1][0] != "":
                    target_manifest_IDs.append(target_dataset[1][0])
                    target_dataset_IDs.append(target_dataset[0][0])

        return synStore, target_manifest_IDs, target_dataset_IDs    

    def list_validation(
        self, val_rule: str, manifest_col: pd.core.series.Series
    ) -> (List[List[str]], List[List[str]], pd.core.series.Series):
        """
        Purpose:
            Determine if values for a particular attribute are comma separated.
        Input:
            - val_rule: str, Validation rule
            - manifest_col: pd.core.series.Series, column for a given attribute
        Returns:
            - manifest_col: Input values in manifest arere-formatted to a list
            - Error log, error list
        """

        # For each 'list' (input as a string with a , delimiter) entered,
        # convert to a real list of strings, with leading and trailing
        # white spaces removed.
        errors = []
        warnings = []
        manifest_col = manifest_col.astype(str)
        csv_re = comma_separated_list_regex()

        rule_parts=val_rule.lower().split(" ")
        if len(rule_parts) > 1:
            list_robustness=rule_parts[1]
        else:
            list_robustness = 'strict'


        if list_robustness == 'strict':
        # This will capture any if an entry is not formatted properly. Only for strict lists
            for i, list_string in enumerate(manifest_col):
                if not re.fullmatch(csv_re,list_string):
                    list_error = "not_comma_delimited"
                    errors.append(
                        GenerateError.generate_list_error(
                            list_string,
                            row_num=str(i + 2),
                            attribute_name=manifest_col.name,
                            list_error=list_error,
                            invalid_entry=manifest_col[i]
                        )
                    )
                

        # Convert string to list.
        manifest_col = parse_str_series_to_list(manifest_col)

        return errors, warnings, manifest_col

    def regex_validation(
        self, val_rule: str, manifest_col: pd.core.series.Series
    ) -> (List[List[str]], List[List[str]]):
        """
        Purpose:
            Check if values for a given manifest attribue conform to the reguar expression,
            provided in val_rule.
        Input:
            - val_rule: str, Validation rule
            - manifest_col: pd.core.series.Series, column for a given
                attribute in the manifest
            Using this module requres validation rules written in the following manner:
                'regex module regular expression'
                - regex: is an exact string specifying that the input is to be validated as a 
                regular expression.
                - module: is the name of the module within re to run ie. search. 
                - regular_expression: is the regular expression with which to validate
                the user input.
        Returns:
            - This function will return errors when the user input value
            does not match schema specifications.
            Logging.error.
            Errors: List[str] Error details for further storage.
        TODO: 
            move validation to convert step.
        """

        reg_exp_rules = val_rule.split(" ")

        try:
            module_to_call = getattr(re, reg_exp_rules[1])
            reg_expression = reg_exp_rules[2]
        except:
            raise ValidationError(
                f"The regex rules were not provided properly for attribute {manifest_col.name}."
                f" They should be provided as follows ['regex', 'module name', 'regular expression']"
            )

        errors = []
        warnings = []
        validation_rules=self.sg.se.get_class_validation_rules(self.sg.se.get_class_label_from_display_name(manifest_col.name))
        # Handle case where validating re's within a list.
        if re.search('list',"|".join(validation_rules)):
            if type(manifest_col[0]) == str:
                # Convert string to list.
                manifest_col = parse_str_series_to_list(manifest_col)

            for i, row_values in enumerate(manifest_col):
                for j, re_to_check in enumerate(row_values):
                    re_to_check = str(re_to_check)
                    if not bool(module_to_call(reg_expression, re_to_check)) and bool(
                        re_to_check
                    ):
                        errors.append(
                            GenerateError.generate_regex_error(
                                val_rule,
                                reg_expression,
                                row_num=str(i + 2),
                                module_to_call=reg_exp_rules[1],
                                attribute_name=manifest_col.name,
                                invalid_entry=manifest_col[i]
                            )
                        )

        # Validating single re's
        else:
            manifest_col = manifest_col.astype(str)
            for i, re_to_check in enumerate(manifest_col):
                if not bool(module_to_call(reg_expression, re_to_check)) and bool(
                    re_to_check
                ):
                    errors.append(
                        GenerateError.generate_regex_error(
                            val_rule,
                            reg_expression,
                            row_num=str(i + 2),
                            module_to_call=reg_exp_rules[1],
                            attribute_name=manifest_col.name,
                            invalid_entry=manifest_col[i]
                        )
                    )

        return errors, warnings

    def type_validation(
        self, val_rule: str, manifest_col: pd.core.series.Series
    ) -> (List[List[str]], List[List[str]]):
        """
        Purpose:
            Check if values for a given manifest attribue are the same type
            specified in val_rule.
        Input:
            - val_rule: str, Validation rule, specifying input type, either
                'float', 'int', 'num', 'str'
            - manifest_col: pd.core.series.Series, column for a given
                attribute in the manifest
        Returns:
            -This function will return errors when the user input value
            does not match schema specifications.
            Logging.error.
            Errors: List[str] Error details for further storage.
        TODO:
            Convert all inputs to .lower() just to prevent any entry errors.
        """
        specified_type = {
            'num': (int, np.int64, float),
            'int': (int, np.int64),
            'float': (float),
            'str': (str),
        }

        errors = []
        warnings = []
        # num indicates either a float or int.
        if val_rule == "num":
            for i, value in enumerate(manifest_col):
                if bool(value) and not isinstance(value, specified_type[val_rule]):
                    errors.append(
                        GenerateError.generate_type_error(
                            val_rule,
                            row_num=str(i + 2),
                            attribute_name=manifest_col.name,
                            invalid_entry=str(manifest_col[i])
                        )
                    )
        elif val_rule in ["int", "float", "str"]:
            for i, value in enumerate(manifest_col):
                if bool(value) and not isinstance(value, specified_type[val_rule]):
                    errors.append(
                        GenerateError.generate_type_error(
                            val_rule,
                            row_num=str(i + 2),
                            attribute_name=manifest_col.name,
                            invalid_entry=str(manifest_col[i])
                        )
                    )
        return errors, warnings

    def url_validation(self, val_rule: str, manifest_col: str) -> (List[List[str]], List[List[str]]):
        """
        Purpose:
            Validate URL's submitted for a particular attribute in a manifest.
            Determine if the URL is valid and contains attributes specified in the
            schema.
        Input:
            - val_rule: str, Validation rule
            - manifest_col: pd.core.series.Series, column for a given
                attribute in the manifest
        Output:
            This function will return errors when the user input value
            does not match schema specifications.
        """

        url_args = val_rule.split(" ")[1:]
        errors = []
        warnings = []

        for i, url in enumerate(manifest_col):
            # Check if a random phrase, string or number was added and
            # log the appropriate error.
            if not isinstance(url,str) or not (
                urlparse(url).scheme
                + urlparse(url).netloc
                + urlparse(url).params
                + urlparse(url).query
                + urlparse(url).fragment
            ):
                #
                url_error = "random_entry"
                valid_url = False
                errors.append(
                    GenerateError.generate_url_error(
                        url,
                        url_error=url_error,
                        row_num=str(i + 2),
                        attribute_name=manifest_col.name,
                        argument=url_args,
                        invalid_entry=manifest_col[i]
                    )
                )
            else:
                # add scheme to the URL if not currently added.
                if not urlparse(url).scheme:
                    url = "http://" + url
                try:
                    # Check that the URL points to a working webpage
                    # if not log the appropriate error.
                    request = Request(url)
                    response = urlopen(request)
                    valid_url = True
                    response_code = response.getcode()
                except:
                    valid_url = False
                    url_error = "invalid_url"
                    errors.append(
                        GenerateError.generate_url_error(
                            url,
                            url_error=url_error,
                            row_num=str(i + 2),
                            attribute_name=manifest_col.name,
                            argument=url_args,
                            invalid_entry=manifest_col[i]
                        )
                    )
                if valid_url == True:
                    # If the URL works, check to see if it contains the proper arguments
                    # as specified in the schema.
                    for arg in url_args:
                        if arg not in url:
                            url_error = "arg_error"
                            errors.append(
                                GenerateError.generate_url_error(
                                    url,
                                    url_error=url_error,
                                    row_num=str(i + 2),
                                    attribute_name=manifest_col.name,
                                    argument=arg,
                                    invalid_entry=manifest_col[i]
                                )
                            )
        return errors, warnings

    def cross_validation(
        self, val_rule: str, manifest_col: pd.core.series.Series, project_scope: List,
    ) -> List[List[str]]:
        """
        Purpose:
            Do cross validation between the current manifest and all other manifests a user has access to on Synapse.
            Check if values in this manifest are present fully in others.
        Input:
            - val_rule: str, Validation rule
            - manifest_col: pd.core.series.Series, column for a given
                attribute in the manifest
        Output:
            This function will return errors when values in the current manifest's attribute 
            are not fully present in the correct amount of other manifests.
        """
        errors = []
        warnings = []
        missing_values = {}
        missing_manifest_log={}
        present_manifest_log=[]
        target_column = pd.Series(dtype=object)
        #parse sources and targets
        source_attribute=manifest_col.name
        [target_component, target_attribute] = val_rule.lower().split(" ")[1].split(".")
        scope=val_rule.lower().split(" ")[2]
        target_column.name=target_attribute

        
        #Get IDs of manifests with target component
        synStore, target_manifest_IDs, target_dataset_IDs = ValidateAttribute.get_target_manifests(target_component,project_scope)

        #Read each manifest
        for target_manifest_ID, target_dataset_ID in zip(target_manifest_IDs,target_dataset_IDs):
            entity = synStore.getDatasetManifest(
                datasetId = target_dataset_ID,
                downloadFile = True
                )
            target_manifest=pd.read_csv(entity.path)

            #convert manifest column names into validation rule input format - 
            column_names={}
            for name in target_manifest.columns:
                column_names[name.replace(" ","").lower()]=name

            if scope.__contains__('set'):
                #If the manifest has the target attribute for the component do the cross validation
                if target_attribute in column_names:                    
                    target_column = target_manifest[column_names[target_attribute]]

                    #Do the validation on both columns
                    missing_values = manifest_col[~manifest_col.isin(target_column)]

                    if missing_values.empty:
                        present_manifest_log.append(target_manifest_ID)
                    else:
                        missing_manifest_log[target_manifest_ID] = missing_values

            elif scope.__contains__('value'):
                if target_attribute in column_names:
                    target_manifest.rename(columns={column_names[target_attribute]: target_attribute}, inplace=True)
                    
                    target_column = pd.concat(
                        objs = [target_column, target_manifest[target_attribute]],
                        join = 'outer',
                        ignore_index= True,
                    )                
                    target_column = target_column.astype('object')
                    #print(target_column)
                    
        
        
        missing_rows=[]
        missing_values=[]  


        if scope.__contains__('value'):
            missing_values = manifest_col[~manifest_col.isin(target_column)]
            duplicated_values = manifest_col[manifest_col.isin(target_column[target_column.duplicated()])]
            
            if val_rule.__contains__('matchAtLeastOne') and not missing_values.empty:
                missing_rows = missing_values.index.to_numpy() + 2
                warnings.append(
                    GenerateError.generate_cross_warning(
                        val_rule = val_rule,
                        row_num = str(list(missing_rows)),
                        attribute_name = source_attribute,
                        invalid_entry = str(missing_values.values.tolist()),
                    )
                )
            elif val_rule.__contains__('matchExactlyOne') and (duplicated_values.any() or missing_values.any()):
                invalid_values  = pd.merge(duplicated_values,missing_values,how='outer')
                invalid_rows    = pd.merge(duplicated_values,missing_values,how='outer',left_index=True,right_index=True).index.to_numpy() + 2
                warnings.append(
                    GenerateError.generate_cross_warning(
                        val_rule = val_rule,
                        row_num = str(list(invalid_rows)), 
                        attribute_name = source_attribute, 
                        invalid_entry = str(pd.Series(invalid_values.squeeze()).values.tolist()) 
                    )
                )
            

            
        #generate warnings if necessary
        elif scope.__contains__('set'):
            if val_rule.__contains__('matchAtLeastOne') and len(present_manifest_log) < 1:     
                missing_entries = list(missing_manifest_log.values()) 
                missing_manifest_IDs = list(missing_manifest_log.keys()) 
                for missing_entry in missing_entries:
                    missing_rows.append(missing_entry.index[0]+2)
                    missing_values.append(missing_entry.values[0])
                    
                missing_rows=list(set(missing_rows))
                missing_values=list(set(missing_values))
                #print(missing_rows,missing_values)

                warnings.append(
                    GenerateError.generate_cross_warning(
                        val_rule = val_rule,
                        row_num = str(missing_rows),
                        attribute_name = source_attribute,
                        invalid_entry = str(missing_values),
                        missing_manifest_ID = missing_manifest_IDs,
                    )
                )
            elif val_rule.__contains__('matchExactlyOne') and len(present_manifest_log) != 1:
                warnings.append(
                    GenerateError.generate_cross_warning(
                        val_rule = val_rule,
                        attribute_name = source_attribute,
                        matching_manifests = present_manifest_log,
                    )
                )
                

        return errors, warnings


