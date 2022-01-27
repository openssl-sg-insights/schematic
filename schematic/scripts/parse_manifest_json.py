'''
Reshape manifest json into CSV that can be easily loaded into
observable. 

Manifest json will give us the requirements and conditional dependencies
then pull in JSON LD to get all the additional information. 
'''

import json
import os
import numpy as np
import pandas as pd
from pathlib import Path

from schematic.utils.io_utils import load_json

DATA_DIR = str(Path('tests/data/visualization').resolve())

def convert_string_cols_to_json(df: pd.DataFrame, cols_to_modify: list):
    """Converts values in a column from strings to JSON list 
    for upload to Synapse.
    Args:

    Returns:
    """
    for col in df.columns:
        if col in cols_to_modify:
            df[col] = df[col].apply(lambda x: json.dumps([y.strip() for y in x]) if x != "NaN" and x  and x == np.nan else x)
    return df

json_path = os.path.join(DATA_DIR, 'json')
csv_output_path = os.path.join(DATA_DIR, 'csv')
jsonld_file_path = os.path.join(DATA_DIR, 'jsonld')


json_file_paths = [os.path.join(json_path, f) for f in os.listdir(json_path) if os.path.isfile(os.path.join(json_path, f))]
jsonld_data_path = [os.path.join(jsonld_file_path, f) for f in os.listdir(jsonld_file_path) if os.path.isfile(os.path.join(jsonld_file_path, f)) and f.endswith('.jsonld')][0]

jsonld_load = load_json(jsonld_data_path)

# For each data type to be loaded gather all attribtes the user would
# have to provide.
df_store = []
for file_path in json_file_paths:
    data_type = file_path.split('/')[-1].split('.')[-3]
    load_data = load_json(file_path)
    data_dict = {}
    # Gather all attribues, their valid values and requirements
    for key, value in load_data['properties'].items():
        data_dict[key] = {}
        for k, v in value.items():
            if k == 'enum':
                data_dict[key]['Valid Values'] = value['enum']
        if key in load_data['required']:
            data_dict[key]['Required'] = True
        else:
            data_dict[key]['Required'] = False
        data_dict[key]['Component'] = data_type
    # Add additional details per key (from the JSON-ld)
    for dic in jsonld_load['@graph']:
        if 'sms:displayName' in dic.keys():
            key = dic['sms:displayName']
            if key in data_dict.keys():
                data_dict[key]['Display Name'] = dic['sms:displayName']
                data_dict[key]['Label'] = dic['rdfs:label']
                data_dict[key]['Comment'] = dic['rdfs:comment']
                if 'validationRules' in dic.keys():
                    breakpoint()
                    data_dict[key]['Validation Rules'] = dic['validationRules']
    # Find conditional dependencies
    if 'allOf' in load_data.keys():
        for conditional_dependencies in load_data['allOf']:
            key = list(conditional_dependencies['then']['properties'])[0]
            try:
                if key in data_dict.keys():
                    if 'Cond_Req' not in data_dict[key].keys():
                        data_dict[key]['Cond_Req'] = []
                        data_dict[key]['Conditional Requirements'] = []
                    
                    attribute = list(conditional_dependencies['if']['properties'])[0]
                    value = conditional_dependencies['if']['properties'][attribute]['enum']
                    conditional_statement = f'{attribute} is "{value[0]}"'
                    if conditional_statement not in data_dict[key]['Conditional Requirements']:
                        data_dict[key]['Cond_Req'] = True
                        data_dict[key]['Conditional Requirements'].extend([conditional_statement])
            except:
                breakpoint()
    for key, value in data_dict.items():
        if 'Conditional Requirements' in value.keys():
            data_dict[key]['Conditional Requirements'] = ' || '.join(data_dict[key]['Conditional Requirements'])
    df = pd.DataFrame(data_dict)
    df = df.T
    cols = ['Display Name', 'Label', 'Comment', 'Required', 'Cond_Req', 'Valid Values', 'Conditional Requirements', 'Validation Rules', 'Component']
    cols = [col for col in cols if col in df.columns]
    df = df[cols]
    df = convert_string_cols_to_json(df, ['Valid Values'])
    df.to_csv(os.path.join(csv_output_path, data_type + '.vis_data.csv'))
    df_store.append(df)

merged_df = pd.concat(df_store)
merged_df = merged_df[cols]
merged_df.to_csv(os.path.join(csv_output_path, 'merged.vis_data.csv'))
