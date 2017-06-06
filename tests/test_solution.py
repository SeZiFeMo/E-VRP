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

from context import solution

class test_solution_module(unittest.TestCase):
    def setUp(self):
        self.sol = solution.Solution()

    def test_is_feasible(self):
        self.assertTrue(self.sol.is_feasible())

class test_route_module(unittest.TestCase):
    def setUp(self):
        self.route = solution.Route()

    def test_is_feasible(self):
        self.assertTrue(self.route.is_feasible())

    def test_raise(self):
        self.assertRaises(solution.UnfeasibleRouteException, raiser)

def raiser():
    raise solution.UnfeasibleRouteException('Exception tester')

if __name__ == '__main__':
    unittest.main(failfast=False)

