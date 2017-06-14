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

import unittest
import networkx as nx

from context import graph
from context import solution


class test_solution_class(unittest.TestCase):

    def setUp(self):
        stub_graph = nx.DiGraph()
        self.sol = solution.Solution(stub_graph)

    def test_is_feasible(self):
        self.assertTrue(self.sol.is_feasible())


class test_route_class(unittest.TestCase):

    def setUp(self):
        alt_lab = 'ASTGTM2_de'
        stub_graph = nx.DiGraph(name=graph.Graph._osm_name)
        # coordinates are (longitude, latitude)
        stub_graph.add_node((16, 48), {alt_lab: 0, 'type': 'depot'})
        stub_graph.add_node((17, 49), {alt_lab: 2, 'type': 'station'})
        stub_graph.add_node((18, 50), {alt_lab: 0, 'type': 'customer'})
        stub_graph.add_node((19, 51), {alt_lab: 4, 'type': ''})
        stub_graph.add_edge((16, 48), (17, 49), {'osm_id': 211937039,
                                                 'length': 20,
                                                 # rise = 2 m
                                                 'speed': 20,
                                                 # energy = 8519818.68 Joule
                                                 # slope = 0.09966865249116 rad
                                                 # time = 0.06 min
                                                 'oneway': False})
        stub_graph.add_edge((17, 49), (18, 50), {'osm_id': 165738417,
                                                 'length': 57,
                                                 # rise = -2 m
                                                 'speed': 20,
                                                 # energy = 24229479.12 Joule
                                                 # slope = -0.0350733305332 rad
                                                 # time = 0.170999999999999 min
                                                 'oneway': False})
        stub_graph.add_edge((18, 50), (16, 48), {'osm_id': 33170597,
                                                 'length': 54,
                                                 # rise = 0 m
                                                 'speed': 45,
                                                 # energy = 22939200.0 Joule
                                                 # slope = 0.0 rad
                                                 # time = 0.072
                                                 'oneway': False})
        stub_graph.add_edge((18, 50), (19, 51), {'osm_id': 12345678,
                                                 'length': 10,
                                                 # rise = 4 m
                                                 'speed': 50,
                                                 # energy = 4295637.36 Joule
                                                 # slope = 0.38050637711236 rad
                                                 # time = 0.012 min
                                                 'oneway': False})

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
        # node can be add after with a for loop
        for coor in [(49, 17, 'station'), (48, 16, 'depot')]:
            route.append(coor)

    def test_is_feasible(self):
        self.assertTrue(self.route.is_feasible(paths=list(), batteries=list()))

    def test_append_node(self):
        node = (49, 17, 'station')
        self.route.append(node)
        self.assertEqual(len(self.route._paths), len(self.route._batteries))

    def test_remove_node(self):
        node = (50, 18, 'customer')
        self.route.append(node)
        self.route.remove(node)
        self.assertEqual(len(self.route._paths), len(self.route._batteries))

    def test_substitute_node(self):
        route = solution.Route(self.cache, greenest=True)
        for coor in [(49, 17, 'station'), (48, 16, 'depot')]:
            route.append(coor)
        node1 = (49, 17, 'station')
        node2 = (50, 18, 'customer')
        route.substitute(node1, node2)
        self.assertEqual(len(self.route._paths), len(self.route._batteries))

    def test_raise(self):
        self.assertRaises(solution.UnfeasibleRouteException, raiser)


def raiser():
    raise solution.UnfeasibleRouteException('Exception tester')


if __name__ == '__main__':
    unittest.main(failfast=False)
