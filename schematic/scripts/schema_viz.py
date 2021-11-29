import argparse
import csv
import numpy as np
import os
from os import walk
from pathlib import Path


import logging

import pandas as pd
import yaml

from schematic.models.visualization import VisualizeModel

from schematic.store.synapse import SynapseStorage
from schematic.utils.io_utils import load_json
from schematic import CONFIG

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

DATA_DIR = os.path.join(os.getcwd(), 'tests', 'data')

# TODO:
# Format citation data in JSONLD format.

class schema_viz():

    def __init__(self,
            ) -> None:

        
        self.path_to_json_ld = self._get_data_path("HTAN_schema_v21_10.model.jsonld")
        self.json_data_model = load_json(self.path_to_json_ld)

        self.viz_model = VisualizeModel(self.path_to_json_ld)
        
    def _get_data_path(self, path, *paths):
        return os.path.join(DATA_DIR, path, *paths)
    
    def _make_output_dir(self):
        parent_path = Path(os.getcwd()).parent
        output_dir = os.path.join(parent_path, 'schema_visisualization_outputs')

        Path(output_dir).mkdir(parents=True, exist_ok=True)
        return output_dir

    def run_viz(self, config, make_interactive, make_dash_cytoscape, make_dash_cytoscape_full,
        make_example):
        '''

        TODO: Clean up how we are passing column types. Perhaps add to the data
        model as an extra column.
        '''
        # Try loading the config file.
        try:
            logger.debug(f"Loading config file contents in '{config}'")
            load_config = CONFIG.load_config(config)
        except ValueError as e:
            logger.error("'--config' not provided or environment variable not set.")
            logger.exception(e)
            sys.exit(1)

        serve_dash = True

        output_dir = self._make_output_dir()
        
        if make_interactive:
            self.viz_model.make_interactive_plot(output_dir, serve_dash)
        
        if make_dash_cytoscape:
            self.viz_model.make_dash_cytograph(output_dir, serve_dash)
        
        if make_dash_cytoscape_full:
            self.viz_model.make_dash_cytograph_full_network(output_dir, serve_dash)
        
        if make_example:
            self.viz_model.make_example_add_nodes(output_dir, serve_dash)

        return 

if __name__ == '__main__':
    # TODO: now that i am pulling in the config file can try to just use that for the input
    # move to using the commands.
    parser = argparse.ArgumentParser(description = 'Create interactive schema visualization prototype')
    parser.add_argument('-config', default='../schematic_package_docs/config.yml')
    parser.add_argument('-make_interactive', default=False, action='store_true')
    parser.add_argument('-make_dash_cytoscape', default=False, action='store_true')
    parser.add_argument('-make_dash_cytoscape_full', default=False, action='store_true')
    parser.add_argument('-make_example', default=False, action='store_true')
    args = parser.parse_args()
    schema_viz().run_viz(args.config, args.make_interactive, args.make_dash_cytoscape,
        args.make_dash_cytoscape_full, args.make_example)
