import json
import logging
import matplotlib.pyplot as plt
import networkx as nx
import os
from os import path
import pandas as pd
from pathlib import Path



# allows specifying explicit variable types
from typing import Any, Dict, Optional, Text, List

from schematic.utils.viz_utils import visualize
from schematic.schemas.explorer import SchemaExplorer
from schematic.schemas.generator import SchemaGenerator
from schematic import LOADER
from schematic.utils.io_utils import load_json


# Make sure to have newest version of decorator


logger = logging.getLogger(__name__)
OUTPUT_DATA_DIR = str(Path('tests/data/visualization').resolve())
DATA_DIR = str(Path('tests/data').resolve())

class get_dependencies(object):
    """
    """

    def __init__(self,
                 path_to_json_ld: str = None,
                 ) -> None:
        # Have take in schema name as an argument
        self.path_to_json_ld = self._get_data_path("HTAN_schema_v21_10.model.jsonld")
        self.json_data_model = load_json(self.path_to_json_ld)

        self.schema_name = path.basename(self.path_to_json_ld).split(".model.jsonld")[0]

        # instantiate a schema generator to retrieve db schema graph from metadata model graph
        self.sg = SchemaGenerator(
                    self.path_to_json_ld
        )

        # Get schema
        self.schema = load_json(self.path_to_json_ld)

        # get metadata model schema graph
        self.G = self.sg.se.get_nx_schema()

    def _get_data_path(self, path, *paths):
        return os.path.join(DATA_DIR, path, *paths)
    
    def _make_output_dir(self):
        parent_path = Path(os.getcwd()).parent
        output_dir = os.path.join(parent_path, 'schema_visisualization_outputs')

        Path(output_dir).mkdir(parents=True, exist_ok=True)
        return output_dir

    
    def find_dependencies(self):
        '''Make standard graphviz network graph
        '''
        csv_output_path = os.path.join(OUTPUT_DATA_DIR, 'csv')
        json_output_path = os.path.join(OUTPUT_DATA_DIR, 'json')
        cdg = self.sg.se.get_digraph_by_edge_type('requiresComponent')
        nodes = cdg.nodes()
        component_highlight = []
        component_normal = []
        for node in nodes:
            highlight_descendants = self.sg.se.get_descendants_by_edge_type(node, 'requiresComponent')
            
            if not highlight_descendants:
                component_highlight.append([node, "id", node])
                normal_descendants = [n for n in nodes if n != node]
            else:
                for hd in highlight_descendants:
                    component_highlight.append([node, "id", hd])
                normal_descendants = [node for node in nodes if node not in highlight_descendants]
            for nd in normal_descendants:
                component_normal.append([node, "id", nd])
        df_h = pd.DataFrame(component_highlight, columns = ['Component', 'type', 'name'])
        df_h.to_csv(os.path.join(csv_output_path, 'highlight_dependencies.csv'))
        js = df_h.to_json(os.path.join(json_output_path,'highlight_dependencies.json'),orient = 'index')

        df_n = pd.DataFrame(component_normal, columns = ['Component', 'type', 'name'])
        df_n.to_csv(os.path.join(csv_output_path, 'normal_dependencies.csv'))
        js = df_n.to_json(os.path.join(json_output_path,'normal_dependencies.json'),orient = 'index')
        return

if __name__ == '__main__':
    get_dependencies().find_dependencies()
    
   