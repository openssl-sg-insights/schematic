import dash
from dash import dcc
from dash import html
import dash_cytoscape as cyto
import graphviz
from graphviz import Source
import json
import logging
import matplotlib.pyplot as plt
import networkx as nx
import os
from os import path
import pandas as pd
import plotly.offline
#import plotly.graph_objs as go
import plotly.graph_objects as go
from pprint import pprint
from dash.dependencies import Input, Output, State
from demos_ import dash_reusable_components as drc

# allows specifying explicit variable types
from typing import Any, Dict, Optional, Text, List

from schematic.utils.viz_utils import visualize
from schematic.schemas.explorer import SchemaExplorer
from schematic.schemas.generator import SchemaGenerator
from schematic import LOADER
from schematic.utils.io_utils import load_json
from schematic import CONFIG

external_stylesheets = [
            {
                "href": "https://fonts.googleapis.com/css2?"
                "family=Lato:wght@400;700&display=swap",
                "rel": "stylesheet",
            },
        ]

default_stylesheet = [
    {
        "selector": 'node',
        'style': {
            "opacity": 0.65,
            'z-index': 9999
        }
    },
    {
        "selector": 'edge',
        'style': {
            "curve-style": "bezier",
            "opacity": 0.45,
            'z-index': 5000
        }
    },
    {
        'selector': '.followerNode',
        'style': {
            'background-color': '#0074D9'
        }
    },
    {
        'selector': '.followerEdge',
        "style": {
            "mid-target-arrow-color": "blue",
            "mid-target-arrow-shape": "vee",
            "line-color": "#0074D9"
        }
    },
    {
        'selector': '.followingNode',
        'style': {
            'background-color': '#FF4136'
        }
    },
    {
        'selector': '.followingEdge',
        "style": {
            "mid-target-arrow-color": "red",
            "mid-target-arrow-shape": "vee",
            "line-color": "#FF4136",
        }
    },
    {
        "selector": '.genesis',
        "style": {
            'background-color': '#B10DC9',
            "border-width": 2,
            "border-color": "purple",
            "border-opacity": 1,
            "opacity": 1,

            "label": "data(label)",
            "color": "#B10DC9",
            "text-opacity": 1,
            "font-size": 12,
            'z-index': 9999
        }
    },
    {
        'selector': ':selected',
        "style": {
            "border-width": 2,
            "border-color": "black",
            "border-opacity": 1,
            "opacity": 1,
            "label": "data(label)",
            "color": "black",
            "font-size": 12,
            'z-index': 9999
        }
    }
]


def _get_data_path(path, *paths):
    return os.path.join(DATA_DIR, path, *paths)
'''
def get_pos(digraph):
        # decode the Digraph to JSON format
        json_string = digraph.pipe('json').decode()

        # parse the resulting json_string
        json_dict = json.loads(json_string)

        # now, you have a JSON dictionary that has two relevant keys:
        # 'objects' for nodes and 'edges' for, well, edges.
        # you can iterate over the nodes and get the (x,y) position for each node as follows:
        pos = {}
        for obj in json_dict['objects']:
            pos[obj['name']] = tuple(
                [float(s)
                for s in obj['pos'].split(',')
                ])
        return pos

def convert_update_pos(pos):
    x_nodes, y_nodes = [], []
    text = []
    if 'HTAN' in path_to_json_ld:
        
        #If this is an HTAN model customize the positioning.
        
        padding = 300
        x_shift_1 = 2500
        x_shift_2 = pos['MelanomaTier3'][0] - \
                    pos['Demographics'][0] + \
                    padding
        y_shift_2 = pos['MelanomaTier3'][1] - \
                    pos['Demographics'][1]
        x_shifted_nodes_1 = ['Patient']
        x_shifted_nodes_2 = [
                           'Demographics',
                           'FamilyHistory',
                           'Exposure',
                           'FollowUp',
                           'Diagnosis',
                           'Therapy',
                           'MolecularTest']
    else:
        padding = 0
        x_shift_1 = 0
        x_shift_2 = 0
        y_shift_2 = 0
        x_shifted_nodes_1 = []
        x_shifted_nodes_2 = []
    
    #Update the positions and format them for plotly.
    for key, value in pos.items():
        if key in x_shifted_nodes_1:
            x_nodes.append(x_shift_1)
            y_nodes.append(value[1])
            pos[key] = (x_shift_1, value[1])
        elif key in x_shifted_nodes_2:
            x_nodes.append(value[0] + x_shift_2)
            y_nodes.append(value[1] + y_shift_2)
            pos[key] = (value[0] + x_shift_2, value[1] + y_shift_2)
        else:
            x_nodes.append(value[0])
            y_nodes.append(value[1])
        text.append(key)
    return x_nodes, y_nodes, text, pos

def get_edge_coords(pos, edges):
    x_edges, y_edges = [], []
    for edge in edges:
        #format: [beginning,ending,None]
        x_coords = [pos[edge[0]][0],pos[edge[1]][0],None]
        x_edges += x_coords

        y_coords = [pos[edge[0]][1],pos[edge[1]][1],None]
        y_edges += y_coords
    return x_edges, y_edges
'''

# Load extra layouts
#cyto.load_extra_layouts()


#asset_path = os.path.join(
#    os.path.dirname(os.path.abspath(__file__)),
#    'assets'
#)

DATA_DIR = os.path.join(os.getcwd(), 'tests', 'data')

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server


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

# Get Node/Edge Positions:
#pos = get_pos(cdg)
#x_nodes, y_nodes, text, pos = convert_update_pos(pos)
#x_edges, y_edges = get_edge_coords(pos, edges)

following_node_di = {}  # user id -> list of users they are following
following_edges_di = {}  # user id -> list of cy edges starting from user id

followers_node_di = {}  # user id -> list of followers (cy_node format)
followers_edges_di = {}  # user id -> list of cy edges ending at user id

cy_edges = []
cy_nodes = []
'''
# Create elements list:
elements_all = []
node_ele_dict = {'data':{}, 'position': {}}
edge_ele_dict = {'data':{}}
for i, name in enumerate(text):
    elements_all.append({
        'data': {'id': name, 'label':name}, 
        'position': {'x': x_nodes[i], 'y': y_nodes[i]}})
for edge in enumerate(cdg.body):
    source_target = edge[1].replace('\t', '').replace('"', '').split(' -> ')
    elements_all.append({
        'data': {'source': source_target[0],
                'target': source_target[1], 
                'label': ' to '.join(source_target)}})
'''
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
    #if source == 'Patient' or target == 'Patient':
        #breakpoint()

genesis_node = [el for el in cy_nodes if el['data']['label'] == 'Patient'][0]
genesis_node['classes'] = "genesis"
default_elements = [genesis_node]


# ################################# APP LAYOUT ################################
styles = {
    'json-output': {
        'overflow-y': 'scroll',
        'height': 'calc(50% - 25px)',
        'border': 'thin lightgrey solid'
    },
    'tab': {'height': 'calc(98vh - 80px)'}
}

app.layout = html.Div(
    children=[
        html.Div(
            children = [
                html.H1(children='HTAN Schema App',
                        className="header-title"),
                html.Div(children='Understanding the network and its dependencies.',
                        className="header-description"),
                ],
            className="header",
            ),
        html.Div(
            children=[
                dcc.Tab(label='Control Panel', children=[
                        drc.NamedRadioItems(
                            name='Expansion Direction',
                            id='radio-expand',
                            options=drc.DropdownOptionsList(
                                'downstream',
                                'upstream'
                            ),
                            value='downstream'
                        )
                    ]),
                ],
            className='card',
            ),
        html.Div( 
            children=[
                cyto.Cytoscape(
                    autoungrabify=True,
                    minZoom=0.2,
                    id='cytoscape',
                    layout={'name': 'breadthfirst'},
                    style={'width': '100%', 'height': '400px'},
                    elements=default_elements,
                    responsive=True),
                ],
            className='card',
            ),
    ],
    className='wrapper'
)


# ############################## CALLBACKS ####################################
@app.callback(Output('cytoscape', 'elements'),
              [Input('cytoscape', 'tapNodeData')],
              [State('cytoscape', 'elements'),
               State('radio-expand', 'value')])
def generate_elements(nodeData, elements, expansion_mode):
    print(nodeData)
    if not nodeData:
        return default_elements

    # If the node has already been expanded, we don't expand it again
    if nodeData.get('expanded'):
        return elements

    # This retrieves the currently selected element, and tag it as expanded
    for element in elements:
        print(element.get('data').get('id'))
        if nodeData['id'] == element.get('data').get('id'):
            #element['data']['expanded'] = True
            break

    if expansion_mode == 'downstream':

        followers_nodes = followers_node_di.get(nodeData['id'])
        followers_edges = followers_edges_di.get(nodeData['id'])

        if followers_nodes:
            for node in followers_nodes:
                node['classes'] = 'followerNode'
            elements.extend(followers_nodes)

        if followers_edges:
            for follower_edge in followers_edges:
                follower_edge['classes'] = 'followerEdge'
            elements.extend(followers_edges)

    elif expansion_mode == 'upstream':

        following_nodes = following_node_di.get(nodeData['id'])
        following_edges = following_edges_di.get(nodeData['id'])

        if following_nodes:
            for node in following_nodes:
                if node['data']['id'] != genesis_node['data']['id']:
                    node['classes'] = 'followingNode'
                    elements.append(node)

        if following_edges:
            for follower_edge in following_edges:
                follower_edge['classes'] = 'followingEdge'
            elements.extend(following_edges)

    
    return elements


if __name__ == '__main__':
    app.run_server(debug=True)