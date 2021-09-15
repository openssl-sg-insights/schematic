import os
import logging

import pytest
import pandas as pd

from schematic.models.visualization import VisualizeModel

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


@pytest.fixture
def viz_model():
    '''
    Note: Json LD needs to have ALL biothings removed or else it
    will put all the biothings in the network too.
    '''
    base_path = '/Users/mialydefelice/Documents/schematic'
    # NF
    #path_to_json_ld = os.path.join(base_path, "schematic/tests/data", "nfti_test.rdb.model.jsonld")
    # HTAN
    path_to_json_ld = os.path.join(base_path, 'test_files', "HTAN_schema_validation_rules_test.model.jsonld")
    viz_model = VisualizeModel(path_to_json_ld)

    yield viz_model

class TestViz:
    def test_viz_schema(self, viz_model):
        output_path = "/Users/mialydefelice/Documents/schematic/schematic/tests/data/"  + "graph_viz.model"
        base_path = "/Users/mialydefelice/Documents/schematic/schematic/tests/data"
        serve_dash = False
        

        # Make various plot types:
        viz_model.make_standard_graph_plot(base_path, 'component_network')
        
        viz_model.make_interactive_plot(base_path, serve_dash)
        
        #viz_model.make_dash_cytograph(base_path, serve_dash)
        
        #output = viz_model.get_plotly(output_path, serve_dash)
        #assert type(output) is dict
