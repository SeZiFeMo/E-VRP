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

import math
import networkx as nx
import unittest

from context import graph
from context import solution


class test_solution_class(unittest.TestCase):

    def setUp(self):
        stub_graph = nx.DiGraph()
        self.sol = solution.Solution(stub_graph)

    def test_is_feasible(self):
        self.assertTrue(self.sol.is_feasible())


class test_route_class(unittest.TestCase):

    depot =        {'lat': 48, 'lon': 16, 'alt':  0, 'type': 'depot'   }
    customers =   [{'lat': 47, 'lon': 15, 'alt':  1, 'type': 'customer'},
                   {'lat': 49, 'lon': 13, 'alt':  0, 'type': 'customer'},
                   {'lat': 50, 'lon': 14, 'alt': -3, 'type': 'customer'}]
    stations =    [{'lat': 48, 'lon': 14, 'alt':  3, 'type': 'station' },
                   {'lat': 47, 'lon': 16, 'alt':  2, 'type': 'station' }]
    other_nodes = [{'lat': 49, 'lon': 15, 'alt':  2, 'type': ''        },
                   {'lat': 50, 'lon': 16, 'alt': -4, 'type': ''        }]

    edges = [{'src_lat': 48, 'src_lon': 16, 'dest_lat': 50, 'dest_lon': 16,
              'speed': 70, 'oneway': False},
             {'src_lat': 50, 'src_lon': 16, 'dest_lat': 50, 'dest_lon': 14,
              'speed': 70, 'oneway': False},
             {'src_lat': 50, 'src_lon': 14, 'dest_lat': 49, 'dest_lon': 15,
              'speed': 30, 'oneway': True},
             {'src_lat': 49, 'src_lon': 15, 'dest_lat': 48, 'dest_lon': 14,
              'speed': 30, 'oneway': True},
             {'src_lat': 48, 'src_lon': 14, 'dest_lat': 49, 'dest_lon': 13,
              'speed': 50, 'oneway': False},
             {'src_lat': 49, 'src_lon': 13, 'dest_lat': 50, 'dest_lon': 14,
              'speed': 50, 'oneway': True},
             {'src_lat': 48, 'src_lon': 14, 'dest_lat': 50, 'dest_lon': 14,
              'speed': 30, 'oneway': True},
             {'src_lat': 48, 'src_lon': 16, 'dest_lat': 49, 'dest_lon': 15,
              'speed': 50, 'oneway': True},
             {'src_lat': 48, 'src_lon': 16, 'dest_lat': 48, 'dest_lon': 14,
              'speed': 30, 'oneway': False},
             {'src_lat': 48, 'src_lon': 14, 'dest_lat': 47, 'dest_lon': 15,
              'speed': 90, 'oneway': False},
             {'src_lat': 47, 'src_lon': 15, 'dest_lat': 47, 'dest_lon': 16,
              'speed': 50, 'oneway': False},
             {'src_lat': 47, 'src_lon': 16, 'dest_lat': 48, 'dest_lon': 16,
              'speed': 50, 'oneway': False}]

    def setUp(self):
        alt_lab = 'ASTGTM2_de'
        stub_graph = nx.DiGraph(name=graph.Graph._osm_name)
        l = [self.depot] + self.customers + self.stations + self.other_nodes
        for node in l:
            # coordinates are (longitude, latitude)
            stub_graph.add_node((node['lon'], node['lat']),
                                 {alt_lab: node['alt'], 'type': node['type']})

        for idx, e in enumerate(self.edges):
            src = next(n for n in l if n['lat'] == e['src_lat'] and
                                       n['lon'] == e['src_lon'])
            dest = next(n for n in l if n['lat'] == e['dest_lat'] and
                                        n['lon'] == e['dest_lon'])
            length = math.sqrt(math.pow(e['src_lat'] - e['dest_lat'], 2) +
                               math.pow(e['src_lon'] - e['dest_lon'], 2) +
                               math.pow(src['alt']   - dest['alt'],   2))

            # coordinates are (longitude, latitude)
            stub_graph.add_edge((e['src_lon'], e['src_lat']),
                                (e['dest_lon'], e['dest_lat']),
                                {'osm_id': idx, 'length': length,
                                 'speed': e['speed'], 'oneway': e['oneway']})

        # self.graph = Graph._get_abstract_graph(stub_graph)  # it is be
        self.graph = graph.Graph(from_DiGraph=stub_graph)     # the same
        # now self.graph has different attributes from stub_graph
        # nodes have: altitude, type, latitude, longitude
        # edges have: osm_id, length, rise, speed, energy, slope, time
        # self.graph nodes have also inverted coordinates (lat, lon)

        self.cache = graph.CachePaths(self.graph)
        self.route = solution.Route(self.cache, greenest=True)

    def test_create_route_with_nodes_list(self):
        # constructor does not get a list of nodes
        route = solution.Route(self.cache, greenest=True)

        # nodes can be added after with a for loop
        nodes_to_add = [(self.customers[0], 'customer'), (self.depot, 'depot')]
        for node, label in nodes_to_add:
            route.append((node['lat'], node['lon'], label))

    def test_is_feasible(self):
        self.assertTrue(self.route.is_feasible(paths=list(), batteries=list()))

    def test_append_node(self):
        node = self.stations[0]['lat'], self.stations[0]['lon'], 'station'
        self.route.append(node)
        self.assertEqual(len(self.route._paths), len(self.route._batteries))

    def test_remove_node(self):
        node = (self.customers[1]['lat'], self.customers[1]['lon'], 'customer')
        self.route.append(node)
        self.route.remove(node)
        self.assertEqual(len(self.route._paths), len(self.route._batteries))

    def test_substitute_node(self):
        route = solution.Route(self.cache, greenest=True)
        nodes_to_add = [(self.customers[2], 'customer'), (self.depot, 'depot')]
        for node, label in nodes_to_add:
            route.append((node['lat'], node['lon'], label))
        new_node = self.stations[1]['lat'], self.stations[1]['lon'], 'station'
        route.substitute(nodes_to_add[0], new_node)
        self.assertEqual(len(self.route._paths), len(self.route._batteries))

    def test_raise(self):
        self.assertRaises(solution.UnfeasibleRouteException, raiser)


def raiser():
    raise solution.UnfeasibleRouteException('Exception tester')


if __name__ == '__main__':
    unittest.main(failfast=False)
