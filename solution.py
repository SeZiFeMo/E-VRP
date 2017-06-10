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

if __name__ == '__main__':
    raise SystemExit('Please do not load that script, run it!')


class Solution(object):

    def __init__(self):
        self.routes = []

    def is_feasible(self):
        return all([route.is_feasible() for route in self.routes])


class Route(object):
    """A Route is a path with some battery information for each node in it."""

    path = None

    battery = None

    def __init__(self, graph, coor_list=None, battery_list=None):
        self.path = Path(graph, coor_list)
        # self.battery = TODO implement a Battery class

    def append(self, node):  # TODO wrap and expand path.append()
        if not self.is_feasible():
            raise UnfeasibleRouteException(
                f'Adding {node} creates a non-feasible route')

    def remove(self, node):  # TODO wrap and expand path.remove
        if not self.is_feasible():
            raise UnfeasibleRouteException(
                f'Removing {node} creates a non-feasible route')

    def substitute(self, node1, node2):  # TODO wrap and expand path.substitute
        if not self.is_feasible():
            raise UnfeasibleRouteException(
                f'Substituting {node1} with {node2} creates a non-feasible route')

    def is_feasible(self):
        """Check the feasibility of the entire Route."""
        return True

class Path(object):
    """A path is a sequence of nodes visited in a given order."""

    __graph = None

    __nodes = None
    """List of nodes, each node is a tuple: ( latitude, longitude, type )."""

    def __init__(self, graph, coor_list=None):
        """Initialize a path from a list of node coordinates."""
        self.__saved = dict()
        self.__graph = graph
        self.__nodes = list()
        if coor_list is None:
            return
        for lat, lon in coor_list:
            self.append(lat, lon, graph.node[(lat, lon)]['type'])

    def __iter__(self):
        """Return iterator over tuple (latitude, longitude, type)."""
        return iter(self.__nodes)

    def __repr__(self):
        return repr(self.__nodes)

    def __str__(self):
        return str(self.__nodes)

    def __sum_over_label(self, label):
        if label not in self.__saved:
            s = sum([self.__graph.edge[src[:2]][self.__nodes[i + 1][:2]][label]
                     for i, src in enumerate(self.__nodes[:-1])])
            self.__saved[label] = s
        return self.__saved[label]

    def append(self, node_latitude, node_longitude, node_type):
        """Insert node in last position of the node list."""
        self.__nodes.append((node_latitude, node_longitude, node_type))

    @property
    def energy(self):
        """Sum of the energies of each edge between the nodes in the list."""
        return self.__sum_over_label('energy')

    @property
    def length(self):
        """Sum of the lengths of each edge between the nodes in the list."""
        return self.__sum_over_label('length')

    def remove(self, node_latitude, node_longitude, node_type=''):
        """Remove from node list the specified node."""
        for index, record in enumerate(self.__nodes):
            if record[:2] == (node_latitude, node_longitude):
                del self.__nodes[index]

    def substitute(self, old_lat, old_lon, new_lat, new_lon):
        """Replace the old node with the new one."""
        for index, record in enumerate(self.__nodes):
            if record[:2] == (old_lat, old_lon):
                record = (new_lat, new_lon,
                          self.__graph.node[(new_lat, new_lon)]['type'])
                self.__nodes[index] = record

    @property
    def time(self):
        """Sum of the times of each edge between the nodes in the list."""
        return self.__sum_over_label('time')

class UnfeasibleRouteException(Exception):

    def __init__(self, msg):
        self._msg = msg
        Exception.__init__(self, msg)

    def __repr__(self):
        return self._msg

    __str__ = __repr__
