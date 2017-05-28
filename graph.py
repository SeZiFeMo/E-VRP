#!/usr/bin/env python3
# coding: utf-8

""" E-VRP is a project about the routing of a fleet of electrical vehicles.

    E-VRP is a project developed for the Application of Operational Research
    exam at University of Modena and Reggio Emilia.

    Copyright (C) 2017  Serena Ziviani, Federico Motta

    This file is part of E-VRP.

    E-VRP is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    any later version.

    E-VRP is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with E-VRP.  If not, see <http://www.gnu.org/licenses/>.
"""

__authors__ = "Serena Ziviani, Federico Motta"
__copyright__ = "E-VRP  Copyright (C)  2017"
__license__ = "GPL3"

# -------------------------------- SCRIPT RUN ------------------------------- #
if __name__ != '__main__':
    print('Please do not load that script, run it!')
    exit(1)

# Add to the following loop every external library used!
for lib in ('matplotlib.pyplot as plt', 'networkx as nx', 'yaml'):
    try:
        exec('import ' + str(lib))
    except ImportError:
        print('Could not import {} library, please install it!'.format(lib))
        exit(1)

import math
import matplotlib.pyplot as plt
import networkx as nx
import os
import warnings
import yaml

import IO
import utility

utility.check_python_version()


def add_slope_to_edge_properties(graph):
    """Compute edges' slope in radians from node distance and altitude."""
    altitude = utility.CLI.args().altitude
    for node1, adjacency_dict in graph.adjacency_iter():
        for node2 in adjacency_dict:
            rise = graph.node[node2][altitude] - graph.node[node1][altitude]
            x1, y1 = node1  # from
            x2, y2 = node2  # to
            run = math.hypot(x2 - x1, y2 - y1)
            slope = math.atan2(rise, run)
            graph.add_edge(node1, node2, attr_dict={'slope':  slope})


def check_problem_solvability(graph):
    """Test if customers and stations are reachable from depot."""
    depot, customers, stations = None, list(), list()
    for node, data in graph.nodes_iter(data=True):
        if data['type'] == 'depot':
            depot = node
        elif data['type'] == 'customer':
            customers.append(node)
        elif data['type'] == 'station':
            stations.append(node)

    quit = False
    for cust in customers:
        if not nx.has_path(graph, depot, cust):
            IO.Log.warning('Customer {} is not reachable '
                           'from the depot'.format(cust))
            quit = True
        if not nx.has_path(graph, cust, depot):
            IO.Log.warning('Depot is not reachable '
                           'from customer {}'.format(cust))
            quit = True

    for stat in stations:
        if not any(nx.has_path(graph, x, stat) for x in [depot] + customers):
            IO.Log.warning('Refueling station {} is not reachable from any '
                           'customer or depot'.format(stat))
        if not any(nx.has_path(graph, stat, x) for x in [depot] + customers):
            IO.Log.warning('No customer or depot reachable from '
                           'refueling station {}'.format(stat))

#    if quit:           # TODO UNCOMMENT
#        exit(1)        # TODO UNCOMMENT


def check_workspace():
    """Ensure workspace exist and it contains only necessary files."""
    ws = utility.CLI.args().workspace
    if not os.path.isdir(ws):
        IO.Log.warning('Directory not found ({})'.format(ws))
        IO.Log.warning('Please set a correct workspace')
        exit(1)

    if not os.path.isfile(os.path.join(ws, 'edges.shp')):
        IO.Log.warning('edges.shp not found in workspace ({})'.format(ws))
        exit(1)

    if not os.path.isfile(os.path.join(ws, 'nodes.shp')):
        IO.Log.warning('nodes.shp not found in workspace ({})'.format(ws))
        exit(1)

    graph_read = nx.read_shp(path=os.path.join(ws, 'nodes.shp'), simplify=True)

    # check each node has an altitude attribute
    altitude = utility.CLI.args().altitude
    for node, data in graph_read.nodes_iter(data=True):
        if altitude not in data:
            IO.Log.warning('Could not find \'{}\' attribute in '
                           'nodes.shp'.format(altitude))
            exit(1)

        # check each altitude attribute is a floating point number
        if not isinstance(data[altitude], float):
            IO.Log.warning('Altitude of node lat: {}, lon {} is not a '
                           'float'.format(*node))
            exit(1)

    for f in os.listdir(ws):
        if f not in [prefix + suffix
                     for prefix in ('nodes.', 'edges.')
                     for suffix in ('dbf', 'shp', 'shx')]:
            IO.Log.warning('Please remove \'{}\''.format(os.path.join(ws, f)))
            exit(1)


def draw(graph):
    """Wrap networkx draw function and suppress its warnings."""
    with warnings.catch_warnings():
        warnings.filterwarnings('ignore', category=UserWarning)
        nx.draw(graph)
    plt.show()


def export_problem_to_directory():
    """Populate directory with a shapefile representation of the problem."""
    export_dir = utility.CLI.args().export_dir
    problem_file = utility.CLI.args().problem_file

    if not os.path.isfile(problem_file):
        IO.Log.warning('Problem file not found ({})'.format(problem_file))
        exit(1)

    if not os.path.isdir(export_dir):
        os.makedirs(export_dir)

    with open(problem_file, 'r') as f:
        problem = yaml.load(f)

    temp_graph = nx.DiGraph()
    temp_graph.add_node((problem['depot']['latitude'],
                         problem['depot']['longitude']))
    nx.write_shp(temp_graph, os.path.join(export_dir, 'depot.shp'))

    temp_graph = nx.DiGraph()
    for node in problem['customers']:
        temp_graph.add_node((node['latitude'],
                             node['longitude']))
    nx.write_shp(temp_graph, os.path.join(export_dir, 'customers.shp'))

    temp_graph = nx.DiGraph()
    for node in problem['stations']:
        temp_graph.add_node((node['latitude'],
                             node['longitude']))
    nx.write_shp(temp_graph, os.path.join(export_dir, 'stations.shp'))

    for ext in ('dbf', 'shp', 'shx'):
        os.remove(os.path.join(export_dir, 'edges.' + ext))

    IO.Log.info('Exported correctly to \'{}\' depot.shp, customers.shp and '
                'stations.shp\n'.format(export_dir))
    exit(0)


def get_abstract_graph(graph):
    """Create a copy of the graph without unnecessary attributes."""
    necessary_edge_attr = ('length', 'oneway', 'osm_id', 'slope', 'speed')
    altitude = utility.CLI.args().altitude
    ret = nx.DiGraph()

    for node, data in graph.nodes_iter(data=True):
        ret.add_node(node, altitude=data[altitude], type=data['type'],
                     longitude=node[0], latitude=node[1])

    for node1, adjacency_dict in graph.adjacency_iter():
        for node2, data in adjacency_dict.items():
            if not all(tag in data for tag in necessary_edge_attr):
                continue

            attr = dict()
            attr['length'] = data['length']
            attr['osm_id'] = data['osm_id']
            attr['slope'] = data['slope']
            if data['speed'] > 0:
                attr['speed'] = data['speed']
            elif 'maxspeed' in data and data['maxspeed'] > 0:
                attr['speed'] = data['maxspeed']
            else:
                attr['speed'] = 50  # default value if no speed available

            ret.add_edge(node1, node2, attr_dict=attr)
            if not data['oneway']:
                attr['slope'] *= -1
                ret.add_edge(node2, node1, attr_dict=attr)

    return ret


def import_shapefile_to_workspace():
    """Populate workspace with translation of import_shapefile into a graph."""
    import_file = utility.CLI.args().import_file
    ws = utility.CLI.args().workspace

    imported_graph = nx.read_shp(path=import_file, simplify=True)
    IO.Log.info('File \'{}\' imported correctly'.format(import_file))

    if not ws:
        IO.Log.warning('Please set workspace dir')
        exit(1)

    nx.write_shp(imported_graph, ws)
    IO.Log.info('Exported correctly to \'{}\' nodes.shp and '
                'edges.shp\n'.format(ws))
    IO.Log.info('PLEASE ADD TO \'{}\' ELEVATION '
                'INFORMATION !'.format(os.path.join(ws, 'nodes.shp')))
    exit(0)


def label_nodes(graph):
    """Ensure problem is applicable to graph and label nodes of interest."""
    problem_file = utility.CLI.args().problem_file

    if not os.path.isfile(problem_file):
        IO.Log.warning('Problem file not found ({})'.format(problem_file))
        exit(1)

    with open(problem_file, 'r') as f:
        problem = yaml.load(f)

    already_labeled_nodes = list()
    depot_coor = (problem['depot']['latitude'], problem['depot']['longitude'])
    if depot_coor not in graph.nodes_iter():
        IO.Log.warning('Could not find depot {} in '
                       ' workspace'.format(depot_coor))
        exit(1)
    graph.node[depot_coor]['type'] = 'depot'
    already_labeled_nodes.append(depot_coor)

    for node in problem['customers']:
        cust_coor = (node['latitude'], node['longitude'])
        if cust_coor not in graph.nodes_iter():
            IO.Log.warning('Could not find customer {} in '
                           ' workspace'.format(cust_coor))
            exit(1)
        if cust_coor in already_labeled_nodes:
            IO.Log.warning('Could not set multiple labels to '
                           'node {} '.format(cust_coor))
            exit(1)
        graph.node[cust_coor]['type'] = 'customer'
        already_labeled_nodes.append(cust_coor)

    for node in problem['stations']:
        station_coor = (node['latitude'], node['longitude'])
        if station_coor not in graph.nodes_iter():
            IO.Log.warning('Could not find station {} in '
                           ' workspace'.format(station_coor))
            exit(1)
        if station_coor in already_labeled_nodes:
            IO.Log.warning('Could not set multiple labels to '
                           'node {} '.format(station_coor))
            exit(1)
        graph.node[station_coor]['type'] = 'station'
        already_labeled_nodes.append(station_coor)

    for node, data in graph.nodes_iter(data=True):
        if 'type' not in data:
            data['type'] = ''


def print_edge_properties(graph, fclass_whitelist=None, tag_blacklist=None):
    """For each edge matching the whitelist print tags not in the blacklist."""
    if fclass_whitelist is None:
        fclass_whitelist = ('living_street', 'motorway', 'motorway_link',
                            'primary', 'primary_link', 'residential',
                            'secondary', 'tertiary', 'unclassified')
    if tag_blacklist is None:
        tag_blacklist = ('code', 'lastchange', 'layer', 'ete', 'ShpName',
                         'Wkb', 'Wkt', 'Json')

    for node1, adjacency_dict in graph.adjacency_iter():
        for node2, data in adjacency_dict.items():
            if 'fclass' not in data or data['fclass'] in fclass_whitelist:
                print('\nLon: {}, Lat: {}  ~>'
                      '  Lon: {}, Lat: {}'.format(node1[0], node1[1],
                                                  node2[0], node2[1]))
                for tag in sorted(data):
                    if tag not in tag_blacklist:
                        print('{}: {}'.format(tag, data[tag]))


class CacheDijkstraPaths(object):
    """Wrap some useful methods around dijkstra's shortest path."""

    __dijkstra = None

    def __init__(self, graph, weight='length',
                 type_whitelist=('depot', 'customer', 'station')):
        """Create cache of shortest paths over a graph."""
        self.__dijkstra = dict()

        # for each depot, customer, station
        for src_node, src_data in graph.nodes_iter(data=True):
            if src_data['type'] in type_whitelist:
                # get distances and paths to all other nodes
                lengths, paths = nx.single_source_dijkstra(graph, src_node,
                                                           weight=weight)
                # for each depot, customer, destination in distances and paths
                for dest_node, dest_data in graph.nodes_iter(data=True):
                    if dest_data['type'] in type_whitelist \
                       and dest_node != src_node \
                       and dest_node in lengths \
                       and dest_node in paths:
                        # cache the distance and the path in a dictionary
                        if src_node not in self.__dijkstra:
                            self.__dijkstra[src_node] = dict()
                        d = {'length': lengths[dest_node],
                             'path': paths[dest_node]}
                        self.__dijkstra[src_node][dest_node] = d

    def get_length(self, src, dest):
        """Raises NetworkXNoPath on cache miss."""
        if src in self.__dijkstra:
            if dest in self.__dijkstra[src]:
                return self.__dijkstra[src][dest]['length']
        raise nx.exception.NetworkXNoPath('Length not found in cache')

    def get_path(self, src, dest):
        """Raises NetworkXNoPath on cache miss."""
        if src in self.__dijkstra:
            if dest in self.__dijkstra[src]:
                return self.__dijkstra[src][dest]['path']
        raise nx.exception.NetworkXNoPath('Path not found in cache')


# ----------------------------------- MAIN ---------------------------------- #

if utility.CLI.args().import_file:
    import_shapefile_to_workspace()  # <-- it always exits

if utility.CLI.args().export_dir:
    export_problem_to_directory()  # <-- it always exits

if utility.CLI.args().workspace is None:
    print('\nFirst of all import a shapefile (-i option) to a workspace '
          'directory (-w option)\n\n'
          'Then run the program specifing the workspace to use '
          '(with -w option)')
    exit(0)

check_workspace()  # <-- it exits if workspace is not compliant

g = nx.read_shp(path=utility.CLI.args().workspace, simplify=True)
add_slope_to_edge_properties(g)
label_nodes(g)  # <-- it exits if problem file is not applicable to graph
check_problem_solvability(g)
abstract_g = get_abstract_graph(g)


dijkstra_graph = nx.DiGraph()
cache = CacheDijkstraPaths(abstract_g)
for coor1, data1 in abstract_g.nodes_iter(data=True):
    if data1['type'] in ('depot', 'customer', 'station'):
        for coor2, data2 in abstract_g.nodes_iter(data=True):
            if data2['type'] in ('depot', 'customer', 'station'):
                # TODO REMOVE TRY-EXCEPT BLOCK
                try:
                    dijkstra_graph.add_edge(coor1, coor2,
                                            {'cost': cache.get_length(coor1,
                                                                      coor2),
                                             'path': cache.get_path(coor1,
                                                                    coor2)})
                except:
                    pass


print('\n' + '#' * 80)
print_edge_properties(dijkstra_graph)
