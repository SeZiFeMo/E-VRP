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

# Add to the following loop every external library used!
for lib in ('graphviz', 'matplotlib.pyplot as plt', 'networkx as nx', 'yaml'):
    try:
        exec('import ' + str(lib))
    except ImportError:
        raise SystemExit(f'Could not import {lib} library, please install it!')

import graphviz
import math
import matplotlib.pyplot as plt
import networkx as nx
import warnings

import heuristic
import IO
import utility
import solution

utility.check_python_version()


class Graph(nx.classes.digraph.DiGraph):
    """Wrapper of two different kind of DiGraph.

       The first one is built from an OpenStreetMap shapefile, while
       the second one is built from the first one, abstracting its essence.
    """

    _osm_name = 'OpenStreetMap_graph'
    """Name given to the osm graph."""

    def __new__(cls, osm_shapefile='', from_DiGraph=None):
        """Return instance of super class."""
        return super(Graph, cls).__new__(cls)

    def __init__(self, *args, **kwargs):
        """Initialize instance of super class."""
        path = kwargs['osm_shapefile'] if 'osm_shapefile' in kwargs else ''
        osm_g = kwargs['from_DiGraph'] if 'from_DiGraph' in kwargs else None

        if isinstance(path, str) and path != '' and osm_g is None:
            super(Graph, self).__init__(data=nx.read_shp(path=path,
                                                         simplify=True),
                                        name=Graph._osm_name)
        elif (path == ''
              and osm_g is not None
              and issubclass(type(osm_g), nx.classes.digraph.DiGraph)):
            super(Graph, self).__init__(data=Graph._get_abstract_graph(osm_g))
        elif (path != ''
              and osm_g is None
              and issubclass(type(path), nx.classes.digraph.DiGraph)):
            super(Graph, self).__init__(data=Graph._get_abstract_graph(path))
        else:
            raise TypeError('Please pass a path to \'osm_shapefile\' or '
                            'a subclass of networkx.classes.digraph.DiGraph '
                            'to \'from_DiGraph\' in constructor Graph().')

    @staticmethod
    def assert_graph_is_osm(graph, method_name):
        """Raise TypeError if self is not an OpenStreetMap graph."""
        if graph.name != Graph._osm_name:
            raise TypeError(f'Method {method_name}() is callable only '
                            'over OpenStreetMap graphs')

    @staticmethod
    def assert_graph_is_abstract(graph, method_name):
        """Raise TypeError if self is not an abstract graph."""
        if graph.name == Graph._osm_name:
            raise TypeError(f'Method {method_name}() is callable only '
                            'over abstract graphs')

    @staticmethod
    def _get_abstract_graph(osm_g):
        """Return a copy of osm_g with only the necessary attributes.

           Fixes osm_g inverted coordinates
           Raises TypeError

           Node attributes:
           - 'altitude':  elevation or height above sea level [meters]
           - 'latitude':  angle with equator                  [decimal degrees]
           - 'longitude': angle with greenwich                [decimal degrees]
           - 'type':      'depot' or 'customer' or 'station' or ''

           Edge attributes:
           - energy: energy spent to traverse a road          [kiloJoule]
           - length:                                          [meters]
           - rise:   altitude difference between dest and src [meters]
           - osm_id: open streetmap identifier of a road
           - slope:  angle describing the steepness of a road [radians]
           - speed:                                           [kilometers/hour]
           - time:   time spent to traverse a road            [minutes]
        """
        Graph.assert_graph_is_osm(osm_g, '_get_abstract_graph')

        necessary_osm_attr = ('length', 'oneway', 'osm_id')
        car = IO.load_problem_file()['car'][1]
        alt = utility.CLI.args().altitude
        ret = nx.DiGraph()

        # note: OpenStreetMap shapefiles have latitude and longitude swapped
        for (lon, lat), data in osm_g.nodes_iter(data=True):
            ret.add_node((lat, lon), altitude=data[alt], type=data['type'],
                         latitude=lat, longitude=lon)

        for (src_lon, src_lat), adjacency_dict in osm_g.adjacency_iter():
            for (dest_lon, dest_lat), data in adjacency_dict.items():
                if not all(tag in data for tag in necessary_osm_attr):
                    continue

                attr = {'osm_id': data['osm_id'],
                        'length': data['length']}
                attr['rise'] = osm_g.node[(dest_lon, dest_lat)][alt]
                attr['rise'] -= osm_g.node[(src_lon, src_lat)][alt]

                if data['speed'] > 0:
                    attr['speed'] = data['speed']
                elif 'maxspeed' in data and data['maxspeed'] > 0:
                    attr['speed'] = data['maxspeed']
                else:
                    attr['speed'] = 50  # default value if no speed available

                attr['energy'] = utility.energy(**attr, **car)
                attr['slope'] = math.atan2(attr['rise'], attr['length'])
                attr['time'] = (attr['length'] / attr['speed']) * 0.06
                ret.add_edge((src_lat, src_lon), (dest_lat, dest_lon),
                             attr_dict=attr)

                if not data['oneway']:
                    attr['rise'] *= -1
                    attr['slope'] *= -1
                    attr['energy'] = utility.energy(**attr, **car)
                    ret.add_edge((dest_lat, dest_lon), (src_lat, src_lon),
                                 attr_dict=attr)
        return ret

    def _nodes_of_interests(self, label):
        """Return cached list of nodes of interests labelled with 'label'."""
        if not hasattr(self, '_' + label):
            # label_nodes() was not called; it should have done this job
            tmp = [(*coor, label) for coor, data in self.nodes_iter(data=True)
                   if data['type'] == label]
            setattr(self, '_' + label, tmp)
        return getattr(self, '_' + label)

    @property
    def depot(self):
        """Return depot coordinates."""
        return self._nodes_of_interests('depot')[0]

    @property
    def customers(self):
        """Return list of customers coordinates."""
        return self._nodes_of_interests('customer')

    @property
    def stations(self):
        """Return list of stations coordinates."""
        return self._nodes_of_interests('station')

    def edge(self, node_src, node_dest):
        """Return properties of edge between src and dest nodes."""
        return super(Graph, self)[node_src[:2]][node_dest[:2]]

    def label_nodes(self, kind='type', lat='latitude', lon='longitude'):
        """Ensure problem file is applicable to graph.

           Nodes of interests are then labelled
           Raises NameError, TypeError
        """
        Graph.assert_graph_is_osm(self, 'label_nodes')

        already_labeled_nodes, problem = list(), IO.load_problem_file()

        for node_type in ('depot', 'customer', 'station'):
            setattr(self, '_' + node_type, list())
            for node in problem[node_type]:
                coor = node[lon], node[lat]
                if coor not in self.nodes_iter():
                    raise NameError(f'Could not find {node_type} {coor} '
                                    'in workspace')
                elif coor in already_labeled_nodes:
                    raise NameError('Could not set multiple labels to node '
                                    f'{coor}')
                else:
                    self.node[coor][kind] = node_type
                    already_labeled_nodes.append(coor)
                    getattr(self, '_' + node_type).append((*coor, node_type))

        for coor, data in self.nodes_iter(data=True):
            if kind not in data:
                data[kind] = ''

    def check_problem_solvability(self, kind='type'):
        """Test if customers and stations are reachable from depot.

           Raises RuntimeError, TypeError
        """
        Graph.assert_graph_is_osm(self, 'check_problem_solvability')

        unsolvable = False
        for *cust_coor, label in self.customers:
            if not nx.has_path(self, self.depot[:2], tuple(cust_coor)):
                IO.Log.warning(f'Customer {c} is not reachable from the depot')
                unsolvable = True
            if not nx.has_path(self, tuple(cust_coor), self.depot[:2]):
                IO.Log.warning(f'Depot is not reachable from customer {c}')
                unsolvable = True

        test_coor = [self.depot] + self.customers
        for *stat_coor, label in self.stations:
            if not any(nx.has_path(self, tuple(src_coor), tuple(stat_coor))
                       for *src_coor, __ in test_coor):
                IO.Log.warning(f'Refueling station {s} is not reachable from '
                               'any customer or depot')
            if not any(nx.has_path(self, tuple(stat_coor), tuple(dest_coor))
                       for *dest_coor, __ in test_coor):
                IO.Log.warning('No customer or depot reachable from '
                               f'refueling station {s}')

        if unsolvable:
            raise RuntimeError('One or more necessary path between the depot '
                               'and the customers were not found')

    def print_edge_properties(self, fclass_whitelist=None, tag_blacklist=None):
        """For each edge in the whitelist print tags not in the blacklist."""
        if fclass_whitelist is None:
            fclass_whitelist = ('living_street', 'motorway', 'motorway_link',
                                'primary', 'primary_link', 'residential',
                                'secondary', 'tertiary', 'unclassified')
        if tag_blacklist is None:
            tag_blacklist = ('code', 'lastchange', 'layer', 'ete',
                             'ShpName', 'Wkb', 'Wkt', 'Json')

        for coor1, adjacency_dict in self.adjacency_iter():
            for coor2, data in adjacency_dict.items():
                if self.name == Graph._osm_name:
                    x1, y1, x2, y2 = *coor1, *coor2
                else:
                    y1, x1, y2, x2 = *coor1, *coor2
                if 'fclass' not in data or data['fclass'] in fclass_whitelist:
                    print(f'\nLat: {y1}, Lon: {x1}  ~>  Lat: {y2}, Lon: {x2}')
                    for tag in sorted(data):
                        if tag not in tag_blacklist:
                            print(f'{tag}: {data[tag]}')


class CachePaths(object):
    """Cache of shortest and most energy-efficient routes."""

    _cache = None
    """List of tuples: ((src_lat, src_lon, src_type),
                        (dest_lat, dest_lon, dest_type),
                        greenest_path,
                        shortest_path)
       where greenest_path and shortest_path are objects of type Path.
    """

    def _add(self, src_node, dest_node, greenest, shortest):
        """Append to cache two new paths between src_node and dest_node.

           greenest and shortest are lists of coordinates (lat, lon)
        """
        if src_node == dest_node:
            return
        record = (src_node, dest_node,
                  solution.Path(self.graph, greenest),
                  solution.Path(self.graph, shortest))
        for index, (s, d, *__) in enumerate(self._cache):
            # update record if already existing
            if (s, d) == (src_node, dest_node):
                self._cache[index] = record
                return
        else:
            self._cache.append(record)

    def __init__(self, graph, type_whitelist=('depot', 'customer', 'station')):
        """Compute shortest and most efficient path.

           Only nodes with labels matching type_whitelist will be considered.
        """
        self._cache = list()
        self._graph = graph
        self._type_whitelist = type_whitelist

        # from each depot, customer, station ...
        for src_coor, src_data in graph.nodes_iter(data=True):
            if src_data['type'] in type_whitelist:
                # get shortest paths starting from src_coor
                shortest_path = nx.single_source_dijkstra_path(graph,
                                                               src_coor,
                                                               weight='lenght')
                # get most energy-efficient paths from src_coor
                greenest_t = nx.bellman_ford(graph, src_coor, weight='energy')
                g_pred, g_energy = greenest_t

                # ... to other depot, customer, destination
                for dest_coor, dest_data in graph.nodes_iter(data=True):
                    if dest_data['type'] in type_whitelist \
                       and dest_coor != src_coor \
                       and dest_coor in shortest_path \
                       and dest_coor in g_energy:
                        # unroll the path from predecessors dictionary
                        greenest_path = list()
                        coor_to_add = dest_coor
                        while coor_to_add is not None:
                            greenest_path.append(coor_to_add)
                            coor_to_add = g_pred[coor_to_add]
                        greenest_path = list(reversed(greenest_path))

                        self._add((*src_coor, src_data['type']),
                                  (*dest_coor, dest_data['type']),
                                  greenest_path,
                                  shortest_path[dest_coor])

    @property
    def graph(self):
        """Return pointer to graph instance."""
        return self._graph

    def greenest(self, src_node, dest_node):
        """Return greenest Path between src_node and dest_node.

           src_node and dest_node are tuples of three elements (lat, lon, type)
        """
        if src_node[2] not in self._type_whitelist:
            raise ValueError(f'source node not in cache {src_node}')
        if dest_node[2] not in self._type_whitelist:
            raise ValueError(f'destination node not in cache {dest_node}')
        try:
            return next(greenest for src, dest, greenest, __ in self._cache
                        if (src, dest) == (src_node, dest_node))
        except StopIteration:
            raise nx.exception.NetworkXNoPath('No greenest path found between '
                                              f'{src_node} and {dest_node}')

    def shortest(self, src_node, dest_node):
        """Return shortest Path between src_node and dest_node.

           src_node and dest_node are tuples of three elements (lat, lon, type)
        """
        if src_node[2] not in self._type_whitelist:
            raise ValueError(f'source node not in cache {src_node}')
        if dest_node[2] not in self._type_whitelist:
            raise ValueError(f'destination node not in cache {dest_node}')
        try:
            return next(shortest for src, dest, __, shortest in self._cache
                        if (src, dest) == (src_node, dest_node))
        except StopIteration:
            raise nx.exception.NetworkXNoPath('No shortest path found between '
                                              f'{src_node} and {dest_node}')

    def destination_iterator(self, dest_node):
        """Return iterator over cached records ending in dest_node.

           dest_node is a tuple of three elements (lat, lon, type) and
           it is omitted from records.
        """
        return iter([(s, green, short)
                     for s, d, green, short in self._cache if d == dest_node])

    def source_iterator(self, src_node):
        """Return iterator over cached records starting from src_node.

           src_node is a tuple of three elements (lat, lon, type) and
           it is omitted from records.
        """
        return iter([(d, green, short)
                     for s, d, green, short in self._cache if s == src_node])


class DrawSVG(object):
    """Create an svg file from either a solution or a route or a path."""

    colors = ('blue', 'green', 'yellow')

    def __init__(self, path, obj, draw_whole_graph=True, color='red'):
        """Create an svg file from passed obj.

           path sould not have an extension!

           Raises TypeError if obj is not a Solution or Route or Path.
        """
        self.path = path
        self.draw_graph = graphviz.Digraph(filename=self.path + '.gv',
                                           engine='neato', format='svg')

        if isinstance(obj, solution.Solution):
            self.graph = obj._graph_cache.graph
            if draw_whole_graph:
                self.add_graph_on_background()

            self.add_solution(obj, color=color)
        elif isinstance(obj, solution.Route):
            self.graph = obj._graph_cache.graph
            if draw_whole_graph:
                self.add_graph_on_background()

            self.add_route(obj, color=color)
        elif isinstance(obj, solution.Path):
            self.graph = obj._graph
            if draw_whole_graph:
                self.add_graph_on_background()

            self.add_path(obj, color=color)
        else:
            raise TypeError('obj passed to DrawSVG() is not a Solution or a '
                            'Route or a Path')

    def save(self, view=False, cleanup=True):
        self.draw_graph.render(filename=self.path, view=view, cleanup=cleanup)

    def add_solution(self, solution, color='black'):
        """Add solution to SVG."""
        for index, route in enumerate(solution.routes):
            self.add_route(route, color=self.colors[index % len(self.colors)])

    def add_route(self, route, color='black'):
        """Add route to SVG."""
        for path in route._paths:
            self.add_path(path, color=color)

    def add_path(self, path, color='black'):
        """Add path to SVG."""
        for node in path:
            self.add_node(node)
        for i, src in enumerate(path._nodes[:-1]):
            dest = path._nodes[i + 1]
            self.add_edge(src, dest, color=color, penwidth='5', style='solid')

    def add_graph_on_background(self):
        for coor, data in self.graph.nodes_iter(data=True):
            self.add_node((*coor, data['type']))

        for src, adj_dict in self.graph.adjacency_iter():
            for dest, data in adj_dict.items():
                self.add_edge(src, dest)

    def add_node(self, node):
        lat, lon, lab = node
        if lab == 'depot':
            shape, color = 'square', 'red'
        elif lab == 'customer':
            shape, color = 'star', 'orange'
        elif lab == 'station':
            shape, color = 'diamond', 'blue'
        else:
            shape, color = 'circle', 'black'
        label = lab + f'\nLat:  {lat:2.7f}\nLon: {lon:2.7f} \n\n\n\n\n '
        self.draw_graph.node(str((lat, lon)), shape=shape, color=color,
                             label=label, fixedsize='true', style='filled',
                             fontsize='18',
                             size='0.5',  # height and width of shape in inch
                             pos=self.coordinates_to_position(lat, lon))

    def add_edge(self, src, dest, color='black', penwidth='1', style='dotted'):
        self.draw_graph.edge(str(src[:2]), str(dest[:2]),
                             color=color, penwidth=penwidth, style=style)

    def coordinates_to_position(self, lat, lon, ppi=72):
        """Return position in points."""
        min_lat = min(lat for lat, lon in self.graph)
        max_lat = max(lat for lat, lon in self.graph)
        min_lon = min(lon for lat, lon in self.graph)
        max_lon = max(lon for lat, lon in self.graph)
        delta_lat = max_lat - min_lat
        delta_lon = max_lon - min_lon
        lat, lon = lat - (delta_lat / 2), lon - (delta_lon / 2)
        if delta_lat > delta_lon:
            x = (8.3 * ppi * lon) / delta_lon
            y = (8.3 * ppi * lat) / delta_lat
        else:
            x = (11.7 * ppi * lon) / delta_lon
            y = (11.7 * ppi * lat) / delta_lat
        return str('%(x)f,%(y)f!' % {'x': x / 10, 'y': y / 10})  # why 10 ?


# ----------------------------------- MAIN ---------------------------------- #
if __name__ == '__main__':
    try:
        if utility.CLI.args().import_file:
            IO.import_shapefile_to_workspace(exit_on_success=True)
        elif utility.CLI.args().export_dir:
            IO.export_problem_to_directory(exit_on_success=True)
        elif utility.CLI.args().workspace is None:
            raise utility.UsageException()

        IO.check_workspace()
    except (FileExistsError, FileNotFoundError) as e:
        print(str(e))
        exit(e.errno)
    except (NameError, TypeError, utility.UsageException) as e:
        print(str(e))
        exit(1)

    try:
        osm_g = Graph(osm_shapefile=utility.CLI.args().workspace)
        osm_g.label_nodes()
        osm_g.check_problem_solvability()
        IO.Log.debug('Graph from shapefile passed solvability tests')

        abstract_g = Graph(from_DiGraph=osm_g)
        IO.Log.debug('Created abstract graph')
    except (NameError, RuntimeError, TypeError) as e:
        print(str(e))
        exit(2)

    cache = CachePaths(abstract_g)
    IO.Log.debug('Created cache over abstract graph')

    # print all paths starting from depot
#    for coor, data in abstract_g.nodes_iter(data=True):
#        src_node = *coor, data['type']
#        if src_node[2] == 'depot':
#            # iterate over path starting from depot
#            for dest_node, green, short in cache.source_iterator(src_node):
#                print(f'shortest path: (length: {short.length}, '
#                      f'energy: {short.energy}, time: {short.time})')
#                for it in short:
#                    print('\tlat: {:2.7f}, lon: {:2.7f}, type: {}'.format(*it))
#
#                print(f'greenest path: (length: {green.length}, '
#                      f'energy: {green.energy}, time: {green.time})')
#                for it in green:
#                    print('\tlat: {:2.7f}, lon: {:2.7f}, type: {}'.format(*it))
#                print('#' * 80)

    # usage of DrawSVG class example
    colors = {'blue': '#0066ff', 'orange': '#ff7f0e', 'green': '#00b300',
              'red': '#d62c27', 'magenta': '#ff47af', 'azure': '#17becf',
              'violet': '#8f5cbd', 'olive': '#adad1f'}

    svg = DrawSVG('route_from_depot_to_first_station',
                  cache.greenest(abstract_g.depot, abstract_g.customers[-1]),color=colors['olive'])
    svg.add_path(cache.greenest(abstract_g.customers[-1], abstract_g.depot),
                 color=colors['azure'])
    svg.save()
#    svg = DrawSVG('route_from_depot_to_first_station',
#                  cache.greenest(abstract_g.depot, abstract_g.customers[-1]))
#    svg.add_path(cache.greenest(abstract_g.customers[-1], abstract_g.depot),
#                 color='green')
#    svg.save()

    # create a greedy heuristic solution
    heur = heuristic.GreedyHeuristic(abstract_g, cache)
    initial_sol = heur.create_feasible_solution()
    IO.Log.info('Greedy solution cost        '
                f'  {initial_sol.time:>9.6f} m, {initial_sol.energy:>10.1f} J')
    DrawSVG('heuristic', initial_sol).save()
    IO.Log.info('Created heuristic.svg')

    # find better solutions with metaheuristic
    meta_sol = heuristic.metaheuristic(initial_sol, max_iter=10**6,
                                       max_time=60 * 10)  # 10 minutes
    IO.Log.info('Metaheuristic solution cost '
                f'  {meta_sol.time:>9.6f} m, {meta_sol.energy:>10.1f} J')
    IO.Log.info('Total gain:                 '
                f'({initial_sol.time - meta_sol.time:>+10.6f} m, '
                f'{initial_sol.energy - meta_sol.energy:>+10.1f} J)')
    DrawSVG('metaheuristic', meta_sol).save()
    IO.Log.info('Created metaheuristic.svg')
