import json
import networkx as nx
import os
from os import path
import pandas as pd
from pprint import pprint

# allows specifying explicit variable types
from typing import Any, Dict, Optional, Text, List

from schematic.utils.viz_utils import visualize
from schematic.schemas.explorer import SchemaExplorer
from schematic.schemas.generator import SchemaGenerator
from schematic.utils.io_utils import load_json


def _get_data_path(path, *paths):
    return os.path.join(DATA_DIR, path, *paths)

DATA_DIR = os.path.join(os.getcwd(), 'tests', 'data')


# ###################### DATA PREPROCESSING ######################
# Load data

path_to_json_ld = _get_data_path("HTAN_schema_v21_10.model.jsonld")

schema_name = path.basename(path_to_json_ld).split(".rdb.model.jsonld")[0]

# instantiate a schema generator to retrieve db schema graph from metadata model graph
sg = SchemaGenerator(path_to_json_ld)

# Get schema
schema = load_json(path_to_json_ld)

# get metadata model schema graph
G = sg.se.get_nx_schema()

# Create Network:
cdg = sg.se.get_digraph_by_edge_type('requiresComponent')
edges = cdg.edges()
cdg = visualize(edges)
nodes = set()

following_node_di = {}  # user id -> list of users they are following
following_edges_di = {}  # user id -> list of cy edges starting from user id

followers_node_di = {}  # user id -> list of followers (cy_node format)
followers_edges_di = {}  # user id -> list of cy edges ending at user id

cy_edges = []
cy_nodes = []

for edge in edges:
    if 'Component' in edge:
        continue
    source = edge[0]
    target = edge[1]

    cy_edge = {'data': {'id': source + ' to ' + target, 'source': source, 'target': target}}
    cy_target = {"data": {"id": target, "label":  target}}
    cy_source = {"data": {"id": source, "label":  source}}

    if source not in nodes:
        nodes.add(source)
        cy_nodes.append(cy_source)
    if target not in nodes:
        nodes.add(target)
        cy_nodes.append(cy_target)

    # Process dictionary of following
    if not following_node_di.get(source):
        following_node_di[source] = []
    if not following_edges_di.get(source):
        following_edges_di[source] = []

    following_node_di[source].append(cy_target)
    following_edges_di[source].append(cy_edge)

    # Process dictionary of followers
    if not followers_node_di.get(target):
        followers_node_di[target] = []
    if not followers_edges_di.get(target):
        followers_edges_di[target] = []

    followers_node_di[target].append(cy_source)
    followers_edges_di[target].append(cy_edge)

genesis_node = [el for el in cy_nodes if el['data']['label'] == 'Patient'][0]
genesis_node['classes'] = "genesis"
default_elements = [genesis_node]

data_store = []
for parent, children in following_node_di.items():
    parent_child_relationships = []
    for child in children:
        child_name = child['data']['label']
        single_pc = {'id': child_name, 'parents': [parent]}
        parent_child_relationships.append(single_pc)
    data_store.append(parent_child_relationships)

'''
Need to structure the data so that it can be more directly imported
into D3.

Need to structure the data into a lits of lists of dictionaries.

Lists represent each level.
Within each level list, there is a dictionary indicating the child and parents
    if applicable.

[
    [{id: 'Demographics'}
    ], # level 1
    [{id: 'Patient', parents:['Demographics']}
    ],
]

'''
# Get max depth of the component network
component_dg = sg.se.get_digraph_by_edge_type('requiresComponent')
component_dg_rev = nx.DiGraph.reverse(component_dg)
component_dg_depth = nx.shortest_path_length(component_dg_rev, source='Demographics')
max_component_depth = max(component_dg_depth.values())
max_depth_components = [
    key 
    for key, value in component_dg_depth.items() 
    if value == max(component_dg_depth.values())
    ]

dependency_dg = sg.se.get_digraph_by_edge_type('requiresDependency')

#Get the max depth of the dependencies off of the terminal component.
dependency_depth = nx.shortest_path_length(dependency_dg, source='Demographics')
dependency_depth_all = []
for component in max_depth_components:
    dependency_depth_all.extend(nx.shortest_path_length(dependency_dg, source=component).values())
max_dependency_depth = max(dependency_depth_all)

# Get the max depth off the 


full_max_depth = max_component_depth + max_dependency_depth
breakpoint()
#full_graph = sg.se.schema_nx
#full_graph_rev = nx.DiGraph.reverse(full_graph)

'''
For each component and dependency get additional information:
'''
class_info = sg.se.explore_class('Biospecimen')

breakpoint()

