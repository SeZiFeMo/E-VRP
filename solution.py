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

# ------------------------------ SCRIPT LOADED ------------------------------ #

import IO

if __name__ == '__main__':
    IO.Log.warning('Please do not load that script, run it!')
    exit(1)

class Solution(object):
    def __init__(self):
        self.routes = []

    def is_feasible(self):
        return all([route.is_feasible() for route in self.routes])


class Route(object):
    def __init__(self):
        self.nodes = {}
        self.time = 0
        pass

    def append(self, node):
        if not is_feasible():
            raise UnfeasibleRouteException(
                    f'Adding {node} creates a non-feasible route')

    def remove(self, node):
        if not is_feasible():
            raise UnfeasibleRouteException(
                    f'Removing {node} creates a non-feasible route')

    def substitute(self, node1, node2):
        if not is_feasible():
            raise UnfeasibleRouteException(
                    f'Substituting {node1} with {node2} creates a non-feasible route')

    def is_feasible(self):
        """Check the feasibility of the entire Route."""
        return True

class UnfeasibleRouteException(Exception):
    def __init__(self, msg):
        self._msg = msg
        Exception.__init__(self, msg)

    def __repr__(self):
        return self._msg

    __str__ = __repr__
