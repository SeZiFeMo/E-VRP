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
    raise SystemExit('Please do not load that script, run it!')

# Add to the following loop every external library used!
for lib in ('matplotlib.pyplot as plt', 'networkx as nx', 'yaml'):
    try:
        exec('import ' + str(lib))
    except ImportError:
        raise SystemExit(f'Could not import {lib} library, please install it!')

import math
import matplotlib.pyplot as plt
import networkx as nx
import warnings

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
    def _get_abstract_graph(osm_g):
        """Return a copy of osm_g with only the necessary attributes.

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
        osm_g.assert_graph_is_osm('_get_abstract_graph')

        necessary_osm_attr = ('length', 'oneway', 'osm_id')
        car = IO.load_problem_file()['car'][1]
        alt = utility.CLI.args().altitude
        ret = nx.DiGraph()

        for node, data in osm_g.nodes_iter(data=True):
            ret.add_node(node, altitude=data[alt], type=data['type'],
                         longitude=node[0], latitude=node[1])

        for src, adjacency_dict in osm_g.adjacency_iter():
            for dest, data in adjacency_dict.items():
                if not all(tag in data for tag in necessary_osm_attr):
                    continue

                attr = {'osm_id': data['osm_id'],
                        'length': data['length'],
                        'rise': osm_g.node[dest][alt] - osm_g.node[src][alt]}

                if data['speed'] > 0:
                    attr['speed'] = data['speed']
                elif 'maxspeed' in data and data['maxspeed'] > 0:
                    attr['speed'] = data['maxspeed']
                else:
                    attr['speed'] = 50  # default value if no speed available

                attr['energy'] = utility.energy(**attr, **car)
                attr['slope'] = math.atan2(attr['rise'], attr['length'])
                attr['time'] = (attr['length'] / attr['speed']) * 0.06
                ret.add_edge(src, dest, attr_dict=attr)

                if not data['oneway']:
                    attr['rise'] *= -1
                    attr['slope'] *= -1
                    attr['energy'] = utility.energy(**attr, **car)
                    ret.add_edge(dest, src, attr_dict=attr)
        return ret

    def _nodes_of_interests(self, label, function='label_nodes()'):
        """Return cached list of nodes of interests labelled with 'label'.

           Raises AttributeError
        """
        label = '_' + label
        if hasattr(self, label) and len(getattr(self, label)) > 1:
            return getattr(self, label)
        elif len(getattr(self, label)) == 1:
            return getattr(self, label)[0]
        raise AttributeError('{} not found, did you call {}?'.format(label[1:],
                                                                     function))

    @property
    def depot(self):
        """Return depot coordinates or raises AttributeError."""
        return self._nodes_of_interests('depot')

    @property
    def customers(self):
        """Return list of customers coordinates or raises AttributeError."""
        return self._nodes_of_interests('customer')

    @property
    def stations(self):
        """Return list of stations coordinates or raises AttributeError."""
        return self._nodes_of_interests('station')

    def edge(self, node_src, node_dest):
        """Return properties of edge between src and dest nodes."""
        return super(Graph, self)[node_src][node_dest]

    def assert_graph_is_osm(self, method_name):
        """Raise TypeError is self is not an OpenStreetMap graph."""
        if self.name != Graph._osm_name:
            raise TypeError(f'Method {method_name}() is callable only '
                            'over OpenStreetMap graphs')

    def assert_graph_is_abstract(self, method_name):
        """Raise TypeError is self is not an abstract graph."""
        if self.name == Graph._osm_name:
            raise TypeError(f'Method {method_name}() is callable only '
                            'over abstract graphs')

    def label_nodes(self, kind='type', lat='latitude', lon='longitude'):
        """Ensure problem file is applicable to graph.

           Nodes of interests are then labelled
           Raises NameError, TypeError
        """
        self.assert_graph_is_osm('label_nodes')

        already_labeled_nodes, problem = list(), IO.load_problem_file()

        for node_type in ('depot', 'customer', 'station'):
            setattr(self, '_' + node_type, list())
            for node in problem[node_type]:
                coor = node[lat], node[lon]
                if coor not in self.nodes_iter():
                    raise NameError(f'Could not find {node_type} {coor} '
                                    'in workspace')
                elif coor in already_labeled_nodes:
                    raise NameError('Could not set multiple labels to node '
                                    f'{coor}')
                else:
                    self.node[coor][kind] = node_type
                    already_labeled_nodes.append(coor)
                    getattr(self, '_' + node_type).append(coor)

        for node, data in self.nodes_iter(data=True):
            if kind not in data:
                data[kind] = ''

    def check_problem_solvability(self, kind='type'):
        """Test if customers and stations are reachable from depot.

           Raises RuntimeError, TypeError
        """
        self.assert_graph_is_osm('check_problem_solvability')

        unsolvable = False
        for c in self.customers:
            if not nx.has_path(self, self.depot, c):
                IO.Log.warning(f'Customer {c} is not reachable from the depot')
                unsolvable = True
            if not nx.has_path(self, c, self.depot):
                IO.Log.warning(f'Depot is not reachable from customer {c}')
                unsolvable = True

        for s in self.stations:
            if not any(nx.has_path(self, x, s)
                       for x in [self.depot] + self.customers):
                IO.Log.warning(f'Refueling station {s} is not reachable from '
                               'any customer or depot')
            if not any(nx.has_path(self, s, x)
                       for x in [self.depot] + self.customers):
                IO.Log.warning('No customer or depot reachable from '
                               f'refueling station {s}')

        if unsolvable:
            raise RuntimeError('One or more necessary path between the depot '
                               'and the customers were not found')

    def draw(self):
        """Wrap networkx draw function and suppress its warnings."""
        with warnings.catch_warnings():
            warnings.filterwarnings('ignore', category=UserWarning)
            nx.draw(self)
        plt.show()

    def print_edge_properties(self, fclass_whitelist=None, tag_blacklist=None):
        """For each edge in the whitelist print tags not in the blacklist."""
        if fclass_whitelist is None:
            fclass_whitelist = ('living_street', 'motorway', 'motorway_link',
                                'primary', 'primary_link', 'residential',
                                'secondary', 'tertiary', 'unclassified')
        if tag_blacklist is None:
            tag_blacklist = ('code', 'lastchange', 'layer', 'ete',
                             'ShpName', 'Wkb', 'Wkt', 'Json')

        for node1, adjacency_dict in self.adjacency_iter():
            for node2, data in adjacency_dict.items():
                if 'fclass' not in data or data['fclass'] in fclass_whitelist:
                    print('\nLon: {}, Lat: {}  ~>'
                          '  Lon: {}, Lat: {}'.format(*node1, *node2))
                    for tag in sorted(data):
                        if tag not in tag_blacklist:
                            print(f'{tag}: {data[tag]}')


class CachePaths(object):
    """Cache of shortest and most energy-efficient routes."""

    _cache = None
    """List of tuples:
       ((src_lat, src_lon), (dst_lat, dst_lon), greenest_path, shortest_path),
       where greenest_path and shortest_path are objects of type Path.
    """

    def _add(self, src, dest, greenest, shortest):
        """Append to cache two new paths between src and dest."""
        if src == dest:
            return
        record = (src, dest,
                  solution.Path(self.graph, greenest),
                  solution.Path(self.graph, shortest))
        for index, (s, d, *_) in enumerate(self._cache):
            # update record if already existing
            if (s, d) == (src, dest):
                self._cache[index] = record
                return
        else:
            self._cache.append(record)

    def __init__(self, graph, type_whitelist=('depot', 'customer', 'station')):
        """Compute shortest and most efficient path."""
        self._cache = list()
        self._graph = graph

        # from each depot, customer, station ...
        for src_node, src_data in graph.nodes_iter(data=True):
            if src_data['type'] in type_whitelist:

                # get shortest paths starting from src_node
                shortest_path = nx.single_source_dijkstra_path(graph,
                                                               src_node,
                                                               weight='lenght')

                # get most energy-efficient paths from src_node
                greenest_t = nx.bellman_ford(graph, src_node, weight='energy')
                g_pred, g_energy = greenest_t

                # ... to other depot, customer, destination
                for dest_node, dest_data in graph.nodes_iter(data=True):
                    if dest_data['type'] in type_whitelist \
                       and dest_node != src_node \
                       and dest_node in shortest_path \
                       and dest_node in g_energy:
                        # unroll the path from predecessors dictionary
                        greenest_path = list()
                        node_to_add = dest_node
                        while node_to_add is not None:
                            greenest_path.append(node_to_add)
                            node_to_add = g_pred[node_to_add]
                        greenest_path = list(reversed(greenest_path))

                        self._add(src_node, dest_node,
                                  greenest_path, shortest_path[dest_node])

    @property
    def graph(self):
        """Return pointer to graph instance."""
        return self._graph

    def greenest(self, src, dest):
        """Return greenest Path between src and dest."""
        for source, destination, greenest, shortest in self._cache:
            if src == source and dest == destination:
                return greenest
        raise nx.exception.NetworkxNoPath('No greenest path found between '
                                          '{} and {}'.format(src, dest))

    def shortest(self, src, dest):
        """Return shortest Path between src and dest."""
        for source, destination, greenest, shortest in self._cache:
            if src == source and dest == destination:
                return shortest
        raise nx.exception.NetworkxNoPath('No greenest path found between '
                                          '{} and {}'.format(src, dest))

    def destination_iterator(self, dest):
        """Return iterator over cached records ending in dest.

           Destination is omitted from records.
        """
        return iter([(src, green, short)
                     for src, d, green, short in self._cache if d == dest])

    def source_iterator(self, src):
        """Return iterator over cached records starting from src.

           Source is omitted from records.
        """
        return iter([(dest, green, short)
                     for s, dest, green, short in self._cache if s == src])


# ----------------------------------- MAIN ---------------------------------- #
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

    abstract_g = Graph(from_DiGraph=osm_g)
except (NameError, RuntimeError, TypeError) as e:
    print(str(e))
    exit(2)


# Usage example
for coor, data in abstract_g.nodes_iter(data=True):
    if data['type'] == 'depot':
        # iterate over path starting from depot
        for dest, green, short in CachePaths(abstract_g).source_iterator(coor):
            print(f'shortest path:  (length: {short.length}, '
                  f'energy: {short.energy}, time: {short.time})')
            for node in short:
                print('\tlat: {:2.7f}, lon: {:2.7f}, type: {}'.format(*node))

            print(f'greenest path:  (length: {green.length}, '
                  f'energy: {green.energy}, time: {green.time})')
            for node in green:
                print('\tlat: {:2.7f}, lon: {:2.7f}, type: {}'.format(*node))
            print('#' * 80)
