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

import copy

import IO

if __name__ == '__main__':
    raise SystemExit('Please do not load that script, run it!')


class Solution(object):
    """A Solution is a list of Routes."""

    def __init__(self, graph):
        self._graph = graph
        self.routes = list()

    def is_feasible(self):
        return all([route.is_feasible() for route in self.routes])


class Route(object):
    """A Route is a path with some battery information for each node in it."""

    def __init__(self, graph, coor_list=None, battery_list=None):
        # FIXME check integrity betweeen coor_list and battery_list
        # this means _at_least_ that len(coor_list) == len(battery_list)
        try:
            if len(coor_list) != len(battery_list):
                IO.Log.error('Length of coordinates and battery '
                             'list are different')
                raise SystemExit()
        except TypeError:
            IO.Log.debug('No battery_list or no coor_list provided')

        self._path = Path(graph, coor_list)
        self._battery = list()

        if battery_list is not None:
            for battery in battery_list:
                self._battery.append(battery)
        # FIXME calculate battery levels from path
        # self.battery = TODO implement a Battery class

    def append(self, node):  # TODO wrap and expand path.append()
        lat, lon, node_type = node
        mod_path = copy.copy(self._path)
        mod_battery = copy.copy(self._battery)
        mod_path.append(lat, lon, node_type)
        mod_battery.append(10)
        # TODO compute battery information

        if self.is_feasible(mod_path, mod_battery):
            self._path = mod_path
            self._battery = mod_battery
        else:
            raise UnfeasibleRouteException(f'Adding {node} creates a '
                                           'non-feasible route')

    def remove(self, node):
        lat, lon, node_type = node
        mod_path = copy.copy(self._path)
        mod_battery = copy.copy(self._battery)
        idx = mod_path.remove(lat, lon, node_type)
        # FIXME calculate new battery level for _all_subsequent_ nodes
        mod_battery.pop(idx)

        if self.is_feasible(mod_path, mod_battery):
            self._path = mod_path
            self._battery = mod_battery
        else:
            raise UnfeasibleRouteException(f'Removing {node} creates a '
                                           'non-feasible route')

    def substitute(self, node1, node2):
        mod_path = copy.copy(self._path)
        mod_battery = copy.copy(self._battery)
        idx = mod_path.substitute(node1[0], node1[1], node2[0], node2[1])
        # FIXME calculate new battery level for this node and
        # _all_subsequent's_
        mod_battery[idx] = 5

        if self.is_feasible(mod_path, mod_battery):
            self._path = mod_path
            self._battery = mod_battery
        else:
            raise UnfeasibleRouteException(f'Substituting {node1} with {node2}'
                                           ' creates a non-feasible route')

    def is_feasible(self, path, battery):
        """Check the feasibility of the entire Route."""
        return True


class Path(object):
    """A path is a sequence of nodes visited in a given order."""

    def __init__(self, graph, coor_list=None):
        """Initialize a path from a list of node coordinates."""
        self._graph = graph
        self._nodes = list()  # each item will be a tuple: ( lat, long, type )
        self._saved = dict()  # empty cache for energy, length and time values

        if coor_list is not None:
            for lat, lon in coor_list:
                self.append(lat, lon)

    def __iter__(self):
        """Return iterator over tuple (latitude, longitude, type)."""
        return iter(self._nodes)

    def __repr__(self):
        return repr(self._nodes)

    def __str__(self):
        return str(self._nodes)

    def _sum_over_label(self, label):
        if label not in self._saved:
            s = sum([self._graph.edge[src[:2]][self._nodes[i + 1][:2]][label]
                     for i, src in enumerate(self._nodes[:-1])])
            self._saved[label] = s
        return self._saved[label]

    @property
    def energy(self):
        """Sum of the energies of each edge between the nodes in the list."""
        return self._sum_over_label('energy')

    @property
    def length(self):
        """Sum of the lengths of each edge between the nodes in the list."""
        return self._sum_over_label('length')

    @property
    def time(self):
        """Sum of the times of each edge between the nodes in the list."""
        return self._sum_over_label('time')

    def append(self, node_latitude, node_longitude, node_type):
        """Insert node in last position of the node list."""
        self._nodes.append((node_latitude, node_longitude, node_type))
        self._saved = dict()  # invalidate cached energy, length and time

    def remove(self, node_latitude, node_longitude, node_type=''):
        """Remove from node list the first occurrence of the specified node."""
        for index, (lat, lon, _) in enumerate(self._nodes):
            if (lat, lon) == (node_latitude, node_longitude):
                self._saved = dict()  # invalidate cached properties
                del self._nodes[index]
                return index

    def substitute(self, old_lat, old_lon, new_lat, new_lon):
        """Replace the first occurrence of the old node with a new one."""
        for index, (lat, lon, _) in enumerate(self._nodes):
            if (lat, lon) == (old_lat, old_lon):
                self._saved = dict()  # invalidate cached properties
                record = (new_lat, new_lon,
                          self._graph.node[(new_lat, new_lon)]['type'])
                self._nodes[index] = record
                return index


class UnfeasibleRouteException(Exception):

    def __init__(self, msg):
        self._msg = msg
        Exception.__init__(self, msg)

    def __repr__(self):
        return self._msg

    __str__ = __repr__
