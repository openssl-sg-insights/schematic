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
                 schema_name: str,
                 ) -> None:
        # Have take in schema name as an argument
        self.schema_name = schema_name
        self.path_to_json_ld = self._get_data_path(schema_name)
        self.json_data_model = load_json(self.path_to_json_ld)

        self.schema_name = path.basename(self.path_to_json_ld).split("rdb.model.jsonld")[0]

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
        csv_output_path = os.path.join(OUTPUT_DATA_DIR, 'NF_csv')
        json_output_path = os.path.join(OUTPUT_DATA_DIR, 'NF_json')
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
        df_h.to_csv(os.path.join(csv_output_path, self.schema_name.split('_')[0] + '_highlight_dependencies.csv'))
        js = df_h.to_json(os.path.join(json_output_path,self.schema_name.split('_')[0] +'_highlight_dependencies.json'),orient = 'index')

        df_n = pd.DataFrame(component_normal, columns = ['Component', 'type', 'name'])
        df_n.to_csv(os.path.join(csv_output_path, self.schema_name.split('_')[0] +'_normal_dependencies.csv'))
        js = df_n.to_json(os.path.join(json_output_path,self.schema_name.split('_')[0] +'_normal_dependencies.json'),orient = 'index')
        return

    def get_tangled_tree_data(self):
        csv_output_path = os.path.join(OUTPUT_DATA_DIR, 'NF_csv')
        json_output_path = os.path.join(OUTPUT_DATA_DIR, 'NF_json')
        cdg = self.sg.se.get_digraph_by_edge_type('requiresComponent')
        nodes = cdg.nodes()
        

        all_dependencies = {}
        parent_relationships = {}
        for node in nodes:
            if node != 'ImagingLevel2Channels':
                parent_relationships[node] = []
        source_nodes = []
        for node in nodes:
            class_info = self.sg.se.explore_class(node)
            if not class_info['component_dependencies']:
                source_nodes.append(node)
            if 'ImagingLevel2Channels' in source_nodes:
                source_nodes.remove('ImagingLevel2Channels')
            rev_cdg = nx.DiGraph.reverse(cdg)
            dependency_depth = nx.shortest_path_length(rev_cdg, source=node)
            all_dependencies[node] = dependency_depth
            for cd in class_info['component_dependencies']:
                if cd != 'ImagingLevel2Channels':
                    try:
                        parent_relationships[node].append(cd)
                    except:
                        breakpoint()

        layers = all_dependencies[source_nodes[0]]
        for n in source_nodes:
            layers[n] = 0
        


        layered_pc = [[] for i in range(0, max(layers.values())+1)]
        for component, i in layers.items():
            if parent_relationships[component]:
                layered_pc[i].append({'id': component, 'parents': parent_relationships[component]})
            else:
                layered_pc[i].append({'id': component})
            #layered_pc[i].append([component, parent_relationships[component]])
        json_string = json.dumps(layered_pc)
        output_file_name = self.schema_name.split('_')[0] + '_tangled_tree.json'
        with open(os.path.join(json_output_path, output_file_name), 'w') as outfile:
            outfile.write(json_string)
        breakpoint()

    def get_tangled_tree_data_2(self):

        csv_output_path = os.path.join(OUTPUT_DATA_DIR, 'NF_csv')
        json_output_path = os.path.join(OUTPUT_DATA_DIR, 'NF_json')
        cdg = self.sg.se.get_digraph_by_edge_type('requiresComponent')
        nodes = cdg.nodes()
        #rev_cdg = nx.DiGraph.reverse(cdg)
        edges = cdg.edges()
        mm_graph = self.sg.se.get_nx_schema()
        subg = self.sg.get_subgraph_by_edge_type(mm_graph, 'requiresComponent')
        topological_gen = list(reversed(list(nx.topological_generations(subg))))
        
        child_parents = {}
        for edge in edges:
            if edge[0] not in child_parents.keys():
                child_parents[edge[0]] = []
            child_parents[edge[0]].append(edge[1])

        num_layers = len(topological_gen)
        layered_pc = [[] for i in range(0, num_layers)]
        for i, component in enumerate(topological_gen):
            try:
                for comp in component:
                    if comp in child_parents.keys():
                        layered_pc[i].append({'id': comp, 'parents': child_parents[comp]})
                    else:
                        layered_pc[i].append({'id': comp})
            except:
                breakpoint()
        json_string = json.dumps(layered_pc)
        output_file_name = self.schema_name.split('_')[0] + '_tangled_tree_test.json'
        with open(os.path.join(json_output_path, output_file_name), 'w') as outfile:
            outfile.write(json_string)
        breakpoint()
        '''
        nodes = cdg.nodes()
        edges = cdg.edges()

        not_source = []
        for node in nodes:
            for edge_pair in edges:
                if node in edge_pair[0]:
                    not_source.append(node)
        source_nodes = []
        for node in nodes:
            if node not in not_source:
                source_nodes.append(node)

        #breakpoint()


        all_dependencies = {}
        all_dependencies_list = []
        parent_relationships = {}
        for node in nodes:
            if node != 'ImagingLevel2Channels':
                parent_relationships[node] = []
        #source_nodes = []
        for node in nodes:
            class_info = self.sg.se.explore_class(node)
            #if not class_info['component_dependencies']:
                #source_nodes.append(node)
            #if 'ImagingLevel2Channels' in source_nodes:
                #source_nodes.remove('ImagingLevel2Channels')
            rev_cdg = nx.DiGraph.reverse(cdg)
            dependency_depth = nx.shortest_path_length(rev_cdg, source=node)
            all_dependencies[node] = dependency_depth
            all_dependencies_list.append([k for k in dependency_depth.keys()])
            for cd in class_info['component_dependencies']:
                if cd != 'ImagingLevel2Channels':
                    try:
                        parent_relationships[node].append(cd)
                    except:
                        breakpoint()
        breakpoint()
                
        
        layers = all_dependencies[source_nodes[0]]
        for n in source_nodes:
            layers[n] = 0
        


        layered_pc = [[] for i in range(0, max(layers.values())+1)]
        for component, i in layers.items():
            if parent_relationships[component]:
                layered_pc[i].append({'id': component, 'parents': parent_relationships[component]})
            else:
                layered_pc[i].append({'id': component})
            #layered_pc[i].append([component, parent_relationships[component]])
        
        json_string = json.dumps(layered_pc)
        output_file_name = self.schema_name.split('_')[0] + '_tangled_tree.json'
        with open(os.path.join(json_output_path, output_file_name), 'w') as outfile:
            outfile.write(json_string)

        '''




        

if __name__ == '__main__':
    #get_dependencies("nf_research_tools.rdb.model.jsonld").find_dependencies()
    #get_dependencies("HTAN_schema_v21_10.model.jsonld").get_tangled_tree_data()
    #get_dependencies("nf_research_tools.rdb.model.jsonld").get_tangled_tree_data_2()

    get_dependencies("HTAN_schema_v21_10.model.jsonld").find_dependencies()
    get_dependencies("HTAN_schema_v21_10.model.jsonld").get_tangled_tree_data_2()

   