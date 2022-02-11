import json
import logging
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
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

        # Get input/output folders
        self.schema_abbr = self.schema_name.split('_')[0]
        self.csv_output_path = self._make_output_dir(self.schema_abbr + '_csv')
        self.json_input_path = self._make_output_dir(self.schema_abbr + '_input_csv')
        self.json_output_path = self._make_output_dir(self.schema_abbr + '_json')

    def _get_data_path(self, path, *paths):
        return os.path.join(DATA_DIR, path, *paths)
    
    def _make_output_dir(self, folder_name):
        output_dir = os.path.join(OUTPUT_DATA_DIR, folder_name)

        Path(output_dir).mkdir(parents=True, exist_ok=True)
        return output_dir

    def strip_double_quotes(self, string):
        if string.startswith('"') and string.endswith('"'):
            string = string[1:-1]
        # now remove whitespace
        string = "".join(string.split())
        return string

    
    def find_dependencies(self, dependency_type, highlight_type):
        '''Make standard graphviz network graph
        '''
        
        cdg = self.sg.se.get_digraph_by_edge_type(dependency_type)
        nodes = cdg.nodes()

        if dependency_type == 'requiresComponent':
            component_nodes = nodes
        else:
            component_dg = self.sg.se.get_digraph_by_edge_type('requiresComponent')
            component_nodes = component_dg.nodes()

        component_highlight = []
        component_normal = []
        for node in component_nodes:
            if highlight_type.lower() == 'all':
                highlight_descendants = self.sg.se.get_descendants_by_edge_type(node, 'requiresComponent')
            elif highlight_type.lower() == 'component_only':
                highlight_descendants = [node]
            if not highlight_descendants:
                component_highlight.append([node, "id", node])
                normal_descendants = [n for n in nodes if n != node]
            else:
                for hd in highlight_descendants:
                    component_highlight.append([node, "id", hd])
                normal_descendants = [node for node in nodes if node not in highlight_descendants]
            for nd in normal_descendants:
                component_normal.append([node, "id", nd])
                
        highlight_file_name = f"{self.schema_abbr}_{dependency_type}_highlight_{highlight_type}.csv"
        df_h = pd.DataFrame(component_highlight, columns = ['Component', 'type', 'name'])
        df_h.to_csv(os.path.join(self.csv_output_path, highlight_file_name))

        normal_file_name = f"{self.schema_abbr}_{dependency_type}_normal_{highlight_type}.csv"
        df_n = pd.DataFrame(component_normal, columns = ['Component', 'type', 'name'])
        df_n.to_csv(os.path.join(self.csv_output_path, normal_file_name))
        return

    def get_topological_generations(self, dependency_type, figure_type):
        '''
        TODO: pull in parse json manifest class so that I can just
        pull the original dictionary and dont have to use the pre-made
        dataframe.
        '''
        digraph = self.sg.se.get_digraph_by_edge_type(dependency_type)
        nodes = digraph.nodes()
        mm_graph = self.sg.se.get_nx_schema()
        subg = self.sg.get_subgraph_by_edge_type(mm_graph, dependency_type)
        # all
        if figure_type == 'all':
            edges = digraph.edges()
            topological_gen = list(reversed(list(nx.topological_generations(subg))))
        # component only
        elif figure_type == 'component_only':
            rev_digraph = nx.DiGraph.reverse(digraph)
            edges = rev_digraph.edges()
            topological_gen = list(nx.topological_generations(subg))
        return topological_gen, nodes, edges

    def find_source_nodes(self, nodes, edges, dependency_type, figure_type, all_attributes=[]):
        '''
        Want to find all nodes in the graph that do not have an upstream node.
        
        For `requiresDependency` we are constraining the graph to dependencies
        per component so dont want to pull in other source nodes.
        
        dependency_type and figure_type pairs:
            `requiresComponent`, `all`
            `requiresDependency`, `all`
            `requiresDependency`, `component_only`
        '''

        not_source = []
        for node in nodes:
            for edge_pair in edges:
                if node == edge_pair[0]:
                    not_source.append(node)
        source_nodes = []
        for node in nodes:
            if dependency_type == 'requiresDependency' and figure_type == 'component_only':
                if node not in not_source and node in all_attributes:
                    source_nodes.append(node)
            else:
                if node not in not_source:
                    source_nodes.append(node)
        return source_nodes

    def get_parent_child_dictionary(self, nodes, edges, figure_type, all_attributes=[]):
        '''
        TODO: find a way to compress this.
        '''

        # all
        if figure_type == 'all':
            child_parents = {}
            for edge in edges:
                if edge[0] not in child_parents.keys():
                    child_parents[edge[0]] = []
                child_parents[edge[0]].append(edge[1])

            parent_children = {}
            for edge in edges:
                if edge[1] not in parent_children.keys():
                    parent_children[edge[1]] = []
                parent_children[edge[1]].append(edge[0])
        
        # component_only
        elif figure_type == 'component_only':
            child_parents = {}
            for edge in edges:
                if edge[0] in all_attributes:
                    if edge[0] not in child_parents.keys():
                        child_parents[edge[0]] = []
                    if edge[1] in all_attributes:
                        child_parents[edge[0]].append(edge[1])

            parent_children = {}
            for edge in edges:
                if edge[1] in all_attributes:
                    if edge[1] not in parent_children.keys():
                        parent_children[edge[1]] = []
                    if edge[0] in all_attributes:
                        parent_children[edge[1]].append(edge[0])

        return child_parents, parent_children

    def get_ca_alias(self, conditional_requirements):
        ca_alias = {}
        for i, req in enumerate(conditional_requirements):
            req = req.split(' || ')
            for r in req:
                attr, alias = r.split(' -is- ')
                attr = "".join(attr.split())
                alias = self.strip_double_quotes(alias)
                ca_alias[alias] = attr
        return ca_alias

    def alias_edges(self, ca_alias, edges):
        new_edges = []
        for i, edge in enumerate(edges):
            edge_set = []
            if edge[0] in ca_alias.keys():
                edge_set.append(ca_alias[edge[0]])
            else:
                edge_set.append(edge[0])
            if edge[1] in ca_alias.keys():
                edge_set.append(ca_alias[edge[1]])
            else:
                edge_set.append(edge[1])
            new_edges.append(edge_set)
        return new_edges

    def prune_topological_gen(self, topological_gen, all_attributes, conditional_attributes):
        '''
        Purpose:
            Remove non-relevant nodes from topological_gen.
                This is necessary since for the figure this function is being used in we 
                only want to display a portion of the graph data.
            In addition to removing non-relevant nodes, we want to add conditional
                attributes to topological_gen so we can visualize them in the tangled tree
                as well.
        Input:
            topological_gen:
            all_attributes:
            conditional_attributes:
        Output:
            new_top_gen: list of lists, mimics structure of topological_gen but only
                includes the nodes we want
        '''


       
        new_top_gen = []
        for i, gen in enumerate(topological_gen):
            gen_value = []
            additional_gen = []
            for k, v in enumerate(gen):
                if v in all_attributes and v not in conditional_attributes:
                    gen_value.append(v)
                if v in conditional_attributes:
                    additional_gen.append(v)
            if gen_value:
                new_top_gen.append(gen_value)
            if additional_gen:
                new_top_gen.append(additional_gen)
        return new_top_gen

    def get_component_layers(self, topological_gen, child_parents, source_nodes, figure_type, cn=''):
        '''
        Purpose:
            Reconfigure topological gen to move things back appropriate layers if 
            they would have a back reference.

            The Tangle Tree figure requrires an acyclic directed graph that has additional 
                layering rules between connected nodes.
                - If there is a backward connection then the line connecting them will
                    break (this would suggest a cyclic connection.)
                - Additionally if two or more nodes are connecting to a downstream node it is 
                    best to put both parent nodes at the same level, if possible, to 
                    prevent line breaks.
                - For aesthetics we also want to move any children nodes one layer below 
                    the parent node(s). If there are multiple parents, put one layer below the
                    parent that is furthest from the origin.

            This is an iterative process that needs to run twice to move all the nodes to their
            appropriate positions.

            It is a bit clunky right now, we could consider rewriting in the future.
        Input:
            topological_gen: list of lists.
            child_parents: dict
            source_nodes: list
            figure_type: str
        Output:
            component_layers: dict, key: component name, value: layer
                represents initial layering of toplogical_gen
            component_layers_copy_copy: dict, key: component name, value: layer
                represents the final layering after moving the components/attributes to
                their desired layer.

        '''


        component_layers = {com:i for i, lev in enumerate(topological_gen)
                                for com in lev}

        component_layers_copy = {com:i for i, lev in enumerate(topological_gen)
                            for com in lev}
        for level in topological_gen:
            for comp in level:
                if comp in child_parents.keys():
                    comp_level = component_layers[comp]
                    parent_levels = []
                    for par in child_parents[comp]:
                        parent_levels.append(component_layers[par])
                        max_parent_level = max(parent_levels)
                        component_layers_copy[comp] = max_parent_level + 1
        component_layers_copy_copy = component_layers_copy
        for level in topological_gen:
            for comp in level:
                if comp in child_parents.keys():
                    comp_level = component_layers[comp]
                    parent_levels = []
                    modify_par = []
                    for par in child_parents[comp]:
                        parent_levels.append(component_layers_copy[par])
                    for par in child_parents[comp]:
                        # if one of the parents is a source node move
                        # it to the same level as the other node the child connects to so
                        # that the connections will not be backwards (and result in a broken line)
                        if figure_type == 'all':
                            if (par in source_nodes and 
                                (parent_levels.count(parent_levels[0]) != len(parent_levels))):
                                parent_levels.pop(-1)
                                modify_par.append(par)
                        elif figure_type == 'component_only':
                            if (par in source_nodes and 
                                (parent_levels.count(parent_levels[0]) != len(parent_levels))
                                and par != cn):
                                parent_levels.pop(-1)
                                modify_par.append(par)
                        max_parent_level = max(parent_levels)
                        component_layers_copy_copy[comp] = max_parent_level + 1
                    for par in modify_par:
                        component_layers_copy_copy[par] = max_parent_level

        return component_layers, component_layers_copy_copy

    def rearrange_topological_gen(self, component_layers_copy_copy, component_layers, topological_gen, figure_type):
        '''
        Reorder components within the topological_generations to match
        how they were ordered in component_layers_copy_copy
        '''
        if figure_type == 'all':
            for key, i in component_layers_copy_copy.items():
                if key not in topological_gen[i]:
                    topological_gen[i].append(key)
                    topological_gen[component_layers[key]].remove(key)
        elif figure_type == 'component_only':
            try:
                for key, i in component_layers_copy_copy.items():
                    # add additional space for conditional dependencies.
                    if i > len(topological_gen) - 1:
                        topological_gen.append([key])
                        topological_gen[component_layers[key]].remove(key)
                    elif key not in topological_gen[i]:
                        topological_gen[i].append(key)
                        topological_gen[component_layers[key]].remove(key)
            except:
                breakpoint()
            
        return topological_gen

    def moves_source_nodes_to_bottom(self, topological_gen, source_nodes):
        # move source nodes to the bottom of their layer in the
        # tangled tree for aesthetics.
        comps_checked = []
        for i, components in enumerate(topological_gen):
            comps_to_move = []
            for comp in components:
                if comp in source_nodes:
                    comps_to_move.append(comp)
            for comp in comps_to_move:
                topological_gen[i].remove(comp)
                topological_gen[i].append(comp)
        return topological_gen

    def get_layers_dict_list(self, topological_gen, child_parents, parent_children):
        num_layers = len(topological_gen)
        layers_list = [[] for i in range(0, num_layers)]
        for i, component in enumerate(topological_gen):
            for comp in component:
                if comp in child_parents.keys():
                    layers_list[i].append({'id': comp, 'parents': child_parents[comp]})
                else:
                    layers_list[i].append({'id': comp})
        return layers_list


    def get_tangled_tree_data(self, dependency_type, figure_type):
        '''
        There are two types of tangled trees we can make right now.
            - `all`
            - `component only`
        This is represented in the prototype observable notebook.
        For `all`: the entire graph will be constructed per dependency type.
            This has been tested for both `requiresComponent` and `requiresDependency`
            for the HTAN data model, and makes tangled trees with 36 and >700 nodes
            respectively.
            `component only`: works with `requiresDependency` (the only one tested) to show all the 
            dependencies required _per_ component.

        dependency_type and figure_type pairs:
            `requiresComponent`, `all`
            `requiresDependency`, `all`
            `requiresDependency`, `component_only`

        To accomodate these very differnt figure constructions the `component_only` 
        the way we will be constructing the data will be slightly differnt.

        The differences will be commented throughout.
        '''
        topological_gen, nodes, edges = self.get_topological_generations(dependency_type, figure_type)
        

        if figure_type == 'all':        
            source_nodes = self.find_source_nodes(nodes, edges, dependency_type, figure_type)
            child_parents, parent_children = self.get_parent_child_dictionary(nodes, edges, figure_type)
            component_layers, component_layers_copy_copy = self.get_component_layers(topological_gen, 
                child_parents, source_nodes, figure_type)
            topological_gen = self.rearrange_topological_gen(component_layers_copy_copy, 
                component_layers, topological_gen, figure_type)
            topological_gen = self.moves_source_nodes_to_bottom(topological_gen, source_nodes)
            layers_dicts = self.get_layers_dict_list(topological_gen, child_parents, parent_children)

            json_string = json.dumps(layers_dicts)
            output_file_name = f"{self.schema_abbr}_tangled_tree.json"
            with open(os.path.join(self.json_output_path, output_file_name), 'w') as outfile:
                outfile.write(json_string)

        # Adding both figure_type and dependency_type as checks since I have not tested
        # other combinations.
        if figure_type == 'component_only' and dependency_type == 'requiresDependency':
            component_dg = self.sg.se.get_digraph_by_edge_type('requiresComponent')
            component_nodes = component_dg.nodes()

            # import the data frame that is made in parse_manifest_json.py
            path_to_attributes_df = str(Path(os.getcwd(), 'tests/data/visualization/HTAN_csv', 
                'merged.vis_data.csv').resolve())
            attributes_df = pd.read_csv(path_to_attributes_df)

            for cn in component_nodes:
                # Gather all component dependency information
                component_attributes = self.sg.get_descendants_by_edge_type(cn, 
                    dependency_type,connected=True)
                
                # Dont want to display `Component` in the figure so remove
                if 'Component' in component_attributes:
                    component_attributes.remove('Component')
                
                # Gather conditional attributes so they can be added to the figure.
                conditional_attributes = list(attributes_df[(attributes_df['Cond_Req']==True)
                    &(attributes_df['Component']==cn)]['Label'])
                ca_df = attributes_df[(attributes_df['Cond_Req']==True)&(attributes_df['Component']==cn)]
                conditional_requirements = list(attributes_df[(attributes_df['Cond_Req']==True)
                    &(attributes_df['Component']==cn)]['Conditional Requirements'])
                all_attributes = list(np.append(component_attributes,conditional_attributes))

                # Gather all source nodes
                source_nodes = self.find_source_nodes(component_nodes, edges, 
                    dependency_type, figure_type, all_attributes)

                # Alias the conditional requirement edge back to its actual parent label,
                # then apply aliasing back to the edges
                ca_alias = self.get_ca_alias(conditional_requirements)
                new_edges = self.alias_edges(ca_alias, edges)

                # Gather relationships between children and their parents.
                child_parents, parent_children = self.get_parent_child_dictionary(nodes,
                    new_edges, figure_type, all_attributes)

                # Remake topological_gen so it has only relevant nodes.
                new_top_gen = self.prune_topological_gen(topological_gen, all_attributes, conditional_attributes)
                
                # Gather components per layer in dictionary form.
                component_layers, component_layers_copy_copy = self.get_component_layers(new_top_gen, 
                    child_parents, source_nodes, figure_type, cn)

                # Rearrange new_top_gen to follow the pattern laid out in component layers.
                new_top_gen = self.rearrange_topological_gen(component_layers_copy_copy, component_layers, new_top_gen, figure_type)
                
                # Move source nodes to the bottom of each layer.
                new_top_gen = self.moves_source_nodes_to_bottom(new_top_gen, source_nodes)
                
                # Create a dictionary of layers that can be used by Observable to create the tangled tree.
                layers_dicts = self.get_layers_dict_list(new_top_gen, child_parents, parent_children)
                
                # Convert dictionary to json strng and save. 
                json_string = json.dumps(layers_dicts)
                output_file_name = f"{self.schema_abbr}_{dependency_type}_{cn}_tangled_tree.json"
                with open(os.path.join(self.json_output_path, output_file_name), 'w') as outfile:
                    outfile.write(json_string)
        return
        

if __name__ == '__main__':

    nf_tools_registry = "nf_research_tools.rdb.model.jsonld"
    HTAN = "HTAN_schema_v21_10.model.jsonld"
    get_dependencies(HTAN).find_dependencies('requiresDependency', 'component_only')
    get_dependencies(HTAN).get_tangled_tree_data('requiresDependency', 'component_only')

   