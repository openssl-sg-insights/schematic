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


# Make sure to have newest version of decorator


logger = logging.getLogger(__name__)

class VisualizeModel(object):
    """
    """

    def __init__(self,
                 path_to_json_ld: str = None,
                 ) -> None:
        self.path_to_json_ld = path_to_json_ld
        self.schema_name = path.basename(self.path_to_json_ld).split(".rdb.model.jsonld")[0]

        # instantiate a schema generator to retrieve db schema graph from metadata model graph
        self.sg = SchemaGenerator(
                    self.path_to_json_ld
        )

        # Get schema
        self.schema = load_json(self.path_to_json_ld)

        # get metadata model schema graph
        self.G = self.sg.se.get_nx_schema()

    def plot_sankey(self, output_path):
        rgba_color = 'rgba(0,0,96,0.2)'
        data = {}
        data['type'] = 'sankey'
        data['domain'] = {'x': [0, 1], 'y': [0, 1]}
        data['orientation'] = 'h'
        data['node'] = {'pad': 15,
                        'thickness': 15,
                        'line': {'color': 'black', 'width': 0.5},
                        'label': ['Resouce', #0
                            'Genetic Reagent', #1
                            'Animal Model', #2
                            'Cell Line', #3
                            'Antibody', #4
                            'Development', #5
                            'Resource Application', #6
                            'Vendor Item', #7
                            'Observation', #8
                            'Donor', #9
                            'Mutation', #10
                            'Investigator', #11
                            'Funder', #12
                            'Publication',#13
                            'Vendor', #14
                            'Biobank', #15
                            ],
                        'x' : [0.1, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.7, 0.7, 0.7, 0.7, 0.7, 0.7, 0.5],
                        'y' : [0.5, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.2, 0.3, 0.6, 0.7, 0.8, 0.5, 0.9],
                        'color': ['rgba(31, 119, 180, 0.8)',
                            'rgba(255, 127, 14, 0.8)',
                            'rgba(44, 160, 44, 0.8)',
                            'rgba(214, 39, 40, 0.8)',
                            'rgba(148, 103, 189, 0.8)',
                            'rgba(140, 86, 75, 0.8)',
                            'rgba(227, 119, 194, 0.8)',
                            'rgba(127, 127, 127, 0.8)',
                            'rgba(188, 189, 34, 0.8)',
                            'rgba(23, 190, 207, 0.8)',
                            'rgba(31, 119, 180, 0.8)',
                            'rgba(255, 127, 14, 0.8)',
                            'rgba(44, 160, 44, 0.8)',
                            'rgba(214, 39, 40, 0.8)',
                            'rgba(148, 103, 189, 0.8)',
                            'rgba(148, 103, 189, 0.8)',
                            ],
                        'pad': 10}
        data['link'] = {'source': [0, 0, 0, 0, 0, 0, 0, 0, 9, 10, 10, 9, 5, 5, 5, 6, 7, 0], 
                        'target': [1, 2, 3, 4, 5, 6, 7, 8, 2, 2, 3, 3, 11, 12, 13, 13, 14, 15], 
                        'value': [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
                        'color': ['rgba_color'] * 18,
                        'label': [''] * 18,
                        }
        fig = go.Figure(data=[go.Sankey(
            #valueformat = ".0f",
            #valuesuffix = "TWh",
            node = dict(
              pad = 15,
              thickness = 15,
              line = dict(color = "black", width = 0.5),
              label =  data['node']['label'],
              color =  data['node']['color']
            ),
            link = dict(
              source =  data['link']['source'],
              target =  data['link']['target'],
              value =  data['link']['value'],
              label =  data['link']['label']
          ))])

        fig.update_layout(
            hovermode = 'x',
            title="NF Database Structure",
            font=dict(size = 10, color = 'white'),
            plot_bgcolor='black',
            paper_bgcolor='black'
        )

        fig.show()
      
        return

    def get_pos(self, digraph):
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

    def convert_update_pos(self, pos):
        x_nodes, y_nodes = [], []
        text = []
        if 'HTAN' in self.path_to_json_ld:
            '''
            If this is an HTAN model customize the positioning.
            '''
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

    def get_edge_coords(self, pos, edges):
        x_edges, y_edges = [], []
        for edge in edges:
            #format: [beginning,ending,None]
            x_coords = [pos[edge[0]][0],pos[edge[1]][0],None]
            x_edges += x_coords

            y_coords = [pos[edge[0]][1],pos[edge[1]][1],None]
            y_edges += y_coords
        return x_edges, y_edges

    def make_standard_graph_plot(self, base_path, network_type):
        '''Make standard graphviz network graph
        '''
        if network_type == 'full_network':
            output_path = base_path + '/full_graph_viz.model'
            full_graph = self.sg.se.full_schema_graph()
            full_graph.render(output_path, view = True)
        elif network_type == 'component_network':
            output_path = base_path + '/component_graph_viz.model'
            cdg = self.sg.se.get_digraph_by_edge_type('requiresComponent')
            edges = cdg.edges()
            cdg = visualize(edges)
            cdg.render(output_path)
        return
    
    def make_interactive_plot(self, base_path, serve_dash):
        external_stylesheets = [
            {
                "href": "https://fonts.googleapis.com/css2?"
                "family=Lato:wght@400;700&display=swap",
                "rel": "stylesheet",
            },
        ]

        output_path = base_path + '/full_graph_viz.model'

        #for full network graph 
        fg_edges = self.G.edges()
        full_graph = visualize(fg_edges)
        # Create Network:

        cdg = self.sg.se.get_digraph_by_edge_type('requiresComponent')
        edges = cdg.edges()
        cdg = visualize(edges)

        # Get Node/Edge Positions:
        pos = self.get_pos(cdg)
        x_nodes, y_nodes, text, pos = self.convert_update_pos(pos)
        x_edges, y_edges = self.get_edge_coords(pos, edges)

        # Retreive the dependencies for each component.
        component_dependencies = {}
        for entry in self.schema['@graph']:
            for component in text:
                if entry['@id'] == 'bts:' + component :
                    if "sms:requiresDependency" in entry.keys():
                        node_dependencies = [
                            i['@id'].replace('bts:','') for i in entry["sms:requiresDependency"]]
                elif component not in component_dependencies.keys():
                    node_dependencies = []
                component_dependencies[component] = node_dependencies

        #create a trace for the edges
        trace_edges = go.Scatter(x=x_edges,
                                y=y_edges,
                                mode='lines',
                                line=dict(color='#2d2d2d', width=2),
                                hoverinfo='none')

        #create a trace for the nodes
        trace_nodes = go.Scatter(x=x_nodes,
                                 y=y_nodes,
                                mode='markers',
                                marker=dict(symbol='circle',
                                            size=15,
                                            color='violet'), #color the nodes according to their community
                                text=text,
                                hoverinfo='text')

        #we need to set the axis for the plot 
        axis = dict(showbackground=False,
                    showline=False,
                    zeroline=False,
                    showgrid=False,
                    showticklabels=False,
                    title='')

        #also need to create the layout for our plot
        layout = go.Layout(title="HTAN Database Network Diagram",
                        width=650,
                        height=625,
                        showlegend=False,
                        scene=dict(xaxis=dict(axis),
                                yaxis=dict(axis),
                                ),
                        margin=dict(t=100),
                        hovermode='closest')

        #Include the traces we want to plot and create a figure
        data = [trace_edges, trace_nodes]
        fig = go.Figure(data=data, layout=layout)
        fig['layout']['yaxis']['autorange'] = "reversed"

        if serve_dash:
            app = dash.Dash(external_stylesheets=external_stylesheets)
            app.layout = html.Div(
                children = [
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
                            html.Div(
                                children=dcc.Graph(figure=fig, config={"displayModeBar": False},)
                                )
                        ],
                        className="card",
                    ),
                ],
                className="wrapper",
            )
            app.run_server(debug=False, use_reloader=False)  # Turn off reloader if inside Jupyter
        else:
            fig.show()

        return

    def make_dash_cytograph(self, base_path, serve_dash):
        output_path = base_path + '/cytograph_viz.model.html'

        # Create Network:
        cdg = self.sg.se.get_digraph_by_edge_type('requiresComponent')
        edges = cdg.edges()
        cdg = visualize(edges)

        # Get Node/Edge Positions:
        pos = self.get_pos(cdg)
        x_nodes, y_nodes, text, pos = self.convert_update_pos(pos)
        x_edges, y_edges = self.get_edge_coords(pos, edges)

        # Create elements list:
        elements = []
        node_ele_dict = {'data':{}, 'position': {}}
        edge_ele_dict = {'data':{}}
        for i, name in enumerate(text):
                elements.append({
                    'data': {'id': name, 'label':name}, 
                    'position': {'x': x_nodes[i], 'y': y_nodes[i]}})
        for edge in enumerate(cdg.body):
                source_target = edge[1].replace('\t', '').replace('"', '').split(' -> ')
                elements.append({
                    'data': {'source': source_target[0],
                            'target': source_target[1], 
                            'label': ' to '.join(source_target)}})
        app = dash.Dash(__name__)
        app.layout = html.Div([
            cyto.Cytoscape(
                id='Cytoscape ',
                layout={'name': 'preset'},
                style={'width': '100%', 'height': '400px'},
                elements=elements,
                responsive=True
            ),
         ])
        app.run_server(debug=True, use_reloader=False)
        #fig.write_html('output_path')

    def make_dash_cytograph_full_network(self, base_path, serve_dash):
        '''
        note this network visualization will take a significant amount of time to 
        make compared to the component network.

        '''

        output_path = base_path + '/cytograph_viz_full_network.model.html'
        
        # Create Network:
        cdg = self.sg.se.get_digraph_by_edge_type('requiresDependency')
        edges = cdg.edges()
        cdg = visualize(edges)

        # Get Node/Edge Positions:
        pos = self.get_pos(cdg)
        x_nodes, y_nodes, text, pos = self.convert_update_pos(pos)
        x_edges, y_edges = self.get_edge_coords(pos, edges)


        '''
        # Create Network:
        edges = self.sg.se.schema_nx.edges()
        # fdg: full digraph
        fdg = self.sg.se.full_schema_graph()

        breakpoint()

        # Get Node/Edge Positions:
        pos = self.get_pos(fdg)
        x_nodes, y_nodes, text, pos = self.convert_update_pos(pos)
        x_edges, y_edges = self.get_edge_coords(pos, edges)
        '''

        # Create elements list:
        elements = []
        node_ele_dict = {'data':{}, 'position': {}}
        edge_ele_dict = {'data':{}}
        for i, name in enumerate(text):
                elements.append({
                    'data': {'id': name, 'label':name}, 
                    'position': {'x': x_nodes[i], 'y': y_nodes[i]}})
        for edge in enumerate(cdg.body):
                source_target = edge[1].replace('\t', '').replace('"', '').split(' -> ')
                elements.append({
                    'data': {'source': source_target[0],
                            'target': source_target[1], 
                            'label': ' to '.join(source_target)}})
        app = dash.Dash(__name__)
        app.layout = html.Div(children = [
            html.H1(children='HTAN Schema Visusualization'),

            html.Div(children='''
                Understanding the network.
            '''),
            cyto.Cytoscape(
                autoungrabify=True,
                minZoom=0.2,
                id='Cytoscape ',
                layout={'name': 'preset'},
                style={'width': '100%', 'height': '400px'},
                elements=elements,
                responsive=True
            ),
         ])
        app.run_server(debug=True, use_reloader=False)
        
        return

    def make_example_add_nodes(self, base_path, serve_dash):
    
        # Load extra layouts
        cyto.load_extra_layouts()


        asset_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            '..', 'assets'
        )

        app = dash.Dash(__name__, assets_folder=asset_path)
        server = app.server


        # ###################### DATA PREPROCESSING ######################
        # Load data
        with open(os.path.join(os.getcwd(), 'schematic', 'scripts', 'demos_', 'data/sample_network.txt'), 'r') as f:
            network_data = f.read().split('\n')

        # We select the first 750 edges and associated nodes for an easier visualization
        edges = network_data[:750]
        nodes = set()

        following_node_di = {}  # user id -> list of users they are following
        following_edges_di = {}  # user id -> list of cy edges starting from user id

        followers_node_di = {}  # user id -> list of followers (cy_node format)
        followers_edges_di = {}  # user id -> list of cy edges ending at user id

        cy_edges = []
        cy_nodes = []

        for edge in edges:
            if " " not in edge:
                continue

            source, target = edge.split(" ")

            cy_edge = {'data': {'id': source+target, 'source': source, 'target': target}}
            cy_target = {"data": {"id": target, "label": "User #" + str(target[-5:])}}
            cy_source = {"data": {"id": source, "label": "User #" + str(source[-5:])}}

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

        genesis_node = cy_nodes[0]
        genesis_node['classes'] = "genesis"
        default_elements = [genesis_node]

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

        # ################################# APP LAYOUT ################################
        styles = {
            'json-output': {
                'overflow-y': 'scroll',
                'height': 'calc(50% - 25px)',
                'border': 'thin lightgrey solid'
            },
            'tab': {'height': 'calc(98vh - 80px)'}
        }

        app.layout = html.Div([
            html.Div(className='four columns', children=[
                dcc.Tabs(id='tabs', children=[
                    dcc.Tab(label='Control Panel', children=[
                        drc.NamedDropdown(
                            name='Layout',
                            id='dropdown-layout',
                            options=drc.DropdownOptionsList(
                                'random',
                                'grid',
                                'circle',
                                'concentric',
                                'breadthfirst',
                                'cose',
                                'cose-bilkent',
                                'dagre',
                                'cola',
                                'klay',
                                'spread',
                                'euler'
                            ),
                            value='grid',
                            clearable=False
                        ),
                        drc.NamedRadioItems(
                            name='Expand',
                            id='radio-expand',
                            options=drc.DropdownOptionsList(
                                'followers',
                                'following'
                            ),
                            value='followers'
                        )
                    ]),

                    dcc.Tab(label='JSON', children=[
                        html.Div(style=styles['tab'], children=[
                            html.P('Node Object JSON:'),
                            html.Pre(
                                id='tap-node-json-output',
                                style=styles['json-output']
                            ),
                            html.P('Edge Object JSON:'),
                            html.Pre(
                                id='tap-edge-json-output',
                                style=styles['json-output']
                            )
                        ])
                    ])
                ]),
            html.Div(className='eight columns', children=[
                cyto.Cytoscape(
                    id='cytoscape',
                    elements=default_elements,
                    stylesheet=default_stylesheet,
                    style={
                        'height': '95vh',
                        'width': '100%'
                    }
                )
            ]),
            ])
        ])
        app.run_server(debug=False, use_reloader=False)


        # ############################## CALLBACKS ####################################
        @app.callback(Output('tap-node-json-output', 'children'),
                      [Input('cytoscape', 'tapNode')])
        def display_tap_node(data):
            return json.dumps(data, indent=2)


        @app.callback(Output('tap-edge-json-output', 'children'),
                      [Input('cytoscape', 'tapEdge')])
        def display_tap_edge(data):
            return json.dumps(data, indent=2)


        @app.callback(Output('cytoscape', 'layout'),
                      [Input('dropdown-layout', 'value')])
        def update_cytoscape_layout(layout):
            return {'name': layout}


        @app.callback(Output('cytoscape', 'elements'),
                      [Input('cytoscape', 'tapNodeData')],
                      [State('cytoscape', 'elements'),
                       State('radio-expand', 'value')])
        def generate_elements(nodeData, elements, expansion_mode):
            if not nodeData:
                return default_elements

            # If the node has already been expanded, we don't expand it again
            if nodeData.get('expanded'):
                return elements

            # This retrieves the currently selected element, and tag it as expanded
            for element in elements:
                if nodeData['id'] == element.get('data').get('id'):
                    element['data']['expanded'] = True
                    break

            if expansion_mode == 'followers':

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

            elif expansion_mode == 'following':

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


    