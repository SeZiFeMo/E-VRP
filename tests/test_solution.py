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

from context import solution

class test_solution_class(unittest.TestCase):
    def setUp(self):
        graph = nx.DiGraph()
        self.sol = solution.Solution()

    def test_is_feasible(self):
        self.assertTrue(self.sol.is_feasible())

class test_route_class(unittest.TestCase):
    def setUp(self):
        self.graph = nx.DiGraph()
        self.graph.add_node((16,48), {'altitude': 1, 'type': 'depot',
                                      'longitude': 16, 'latitude': 48})
        self.graph.add_node((17,49), {'altitude': 2, 'type': 'station',
                                      'longitude': 17, 'latitude': 49})
        self.graph.add_node((18,50), {'altitude': 3, 'type': 'customer',
                                      'longitude': 18, 'latitude': 50})
        self.graph.add_node((19,51), {'altitude': 4, 'type': '',
                                      'longitude': 19, 'latitude': 51})
        self.route = solution.Route(self.graph)

    def test_create_route_with_nodes_list(self):
        route = solution.Route(self.graph, [(16,48),(19,51)])

    def test_is_feasible(self):
        self.assertTrue(self.route.is_feasible())

    def test_raise(self):
        self.assertRaises(solution.UnfeasibleRouteException, raiser)

def raiser():
    raise solution.UnfeasibleRouteException('Exception tester')

if __name__ == '__main__':
    unittest.main(failfast=False)

