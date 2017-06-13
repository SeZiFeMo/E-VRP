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
import networkx as nx

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
    """A Route is a list of Path with the tail-head nodes in common.

       Example: [ Path_from_A_to_B,
                  Path_from_B_to_C,
                  Path_from_C_to_D,
                        ...
                  Path_from_L_to_M ]

       For each tail-node (in the example: B, C, D, ... M) of a Path
       a battery instance stores energy level/progress/history.
    """

    def __init__(self, graph_cache, greenest=False, shortest=False):
        """Raises ValueError if flag are not opposite."""
        if bool(greenest) == bool(shortest):
            raise ValueError('Please set either greenest or shortest flag')
        self.greenest, self.shortest = bool(greenest), bool(shortest)

        self._graph_cache = graph_cache
        self._paths, self._batteries = list(), list()
        self.time_limit = IO.load_problem_file()['time_limit']

    def append(self, dest_node):
        """Add to route the path to reach dest_node from previous last node.

           Example:
           route = [ Path_from_A_to_B, ... Path_from_L_to_M ]
           route.append(coor_of_node_N)
           route = [ Path_from_A_to_B, ... Path_from_L_to_M, Path_from_M_to_N ]

           Raises:
           - UnfeasibleRouteException (without modifing current route)
           - ValueError if nor greenest or shortest flags is set
        """
        path = self.default_path(self.last_node(with_type=False), dest_node)

        if path.time + sum(p.time for p in self._paths) > self.time_limit:
            raise UnfeasibleRouteException('Time limit exceeeded')

        batt = copy.copy(self.last_battery())
        batt.charge -= path.energy  # could raise UnfeasibleRouteException

        # it's safe to append path to route because it's feasible
        self._paths.append(path)
        self._batteries.append(batt)

    def remove(self, rm_node):
        """Remove the first path ending with node and the next one.

           Example:
           route = [ Path_from_A_to_B, Path_from_B_to_C, ... Path_from_L_to_M ]
           route.remove(coor_of_node_B)
           route = [ Path_from_A_to_C, ... Path_from_L_to_M ]

           Raises:
           - UnfeasibleRouteException (without modifing current route)
           - ValueError if nor greenest or shortest flags is set
        """
        try:
            idx = next(index for index, path in enumerate(self._paths)
                       if path.last_node() == rm_node[:2])
        except StopIteration:
            # rm_node not found in self._paths
            return

        nodes_to_append = [p.last_node() for p in self._paths[idx:]]

        # backup and cut paths and batteries
        path_bkp, batt_bkp = copy.copy(self._paths), copy.copy(self._batteries)
        self._paths, self._batteries = self._paths[:idx], self._batteries[:idx]

        try:
            for coor in nodes_to_append:
                self.append(coor)
        except UnfeasibleRouteException as e:
            self._paths, self._batteries = path_bkp, batt_bkp
            raise e

    def substitute(self, old_node, new_node):
        """Substitute the first path ending with old_node and the next one.

           Example:
           route = [ Path_from_A_to_B, Path_from_B_to_C, ... Path_from_L_to_M ]
           route.substitute(coor_of_node_B, coor_of_S)
           route = [ Path_from_A_to_S, Path_from_S_to_C, ... Path_from_L_to_M ]

           Raises:
           - UnfeasibleRouteException (without modifing current route)
           - ValueError if new_node is already in route
        """
        try:
            idx = next(index for index, path in enumerate(self._paths)
                       if path.last_node() == old_node[:2])
        except StopIteration:
            # old_node not found in self._paths
            return

        nodes_to_append = [p.last_node() for p in self._paths[idx:]]

        if new_node in nodes_to_append:
            raise ValueError('Could not substitute node with another one '
                             'already in route')

        # backup and cut paths and batteries
        path_bkp, batt_bkp = copy.copy(self._paths), copy.copy(self._batteries)
        self._paths, self._batteries = self._paths[:idx], self._batteries[:idx]

        try:
            for coor in [new_node] + nodes_to_append:
                self.append(coor)
        except UnfeasibleRouteException as e:
            self._paths, self._batteries = path_bkp, batt_bkp
            raise e

    def is_feasible(self, paths, batteries):
        """Return if Route feasibility check is passed.

           Otherwise raises UnfeasibleRouteException
        """
        time_test = 0
        batt_test = Battery()
        for i, (*src, src_type) in enumerate(paths[:-1]):
            *dest, dest_type = paths[i + 1]
            path = self.default_path(src, dest)

            batt_test.charge -= path.energy
            time_test += path.time

            # if energy sum is not zero a charge might have happened
            e_sum = batteries[i + 1].charge - batteries[i].charg + path.energy
            if abs(e_sum) > 0 and dest_type == 'station':
                time_test += batt_test.recharge_until(batteries[i + 1].charge)
            elif abs(e_sum) > 0:
                raise UnfeasibleRouteException('Could not charge battery '
                                               'outside stations')

            if time_test > self.time_limit:
                raise UnfeasibleRouteException('Time limit exceeded')
        return True

    def last_battery(self):
        """Return battery status at last reached node.

           A full battery is returned on empty route.
        """
        if not self._batteries:
            return Battery()
        return self._batteries[-1]

    def last_node(self, with_type=True):
        """Return (latitude, longitude, type) of last reached node.

           Depot is returned on empty route.
        """
        if not self._paths:
            return self._graph_cache.graph().depot
        return self._paths[-1].last_node(with_type=with_type)

    def default_path(self, src_node, dest_node):
        """Return greenest or shortest path between src and dest.

           Raises:
           - UnfeasibleRouteException if there is no path between src and dest
           - ValueError if nor greenest or shortest flags is set
        """
        try:
            if self.greenest:
                return self._graph_cache.greenest(src_node, dest_node)
            elif self.shortest:
                return self._graph_cache.shortest(src_node, dest_node)
            else:
                raise ValueError('Both greenest and shortest flag are off')
        except nx.exception.NetworkxNoPath as e:
            raise UnfeasibleRouteException(str(e))


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

    def append(self, node_latitude, node_longitude, node_type=None):
        """Insert node in last position of the node list."""
        if node_type is None:
            node_type = self._graph.node[(node_latitude,
                                          node_longitude)]['type']
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

    def first_node(self, with_type=False):
        """Return first item or nodes.

           Raises IndexError if path is empty
        """
        if not self._nodes:
            raise IndexError('Could not get first node from empty path')
        if with_type:
            return self._nodes[0]
        else:
            return self._nodes[0][:2]

    def last_node(self, with_type=False):
        """Return first item or nodes.

           Raises IndexError if path is empty
        """
        if not self._nodes:
            raise IndexError('Could not get last node from empty path')
        if with_type:
            return self._nodes[-1]
        else:
            return self._nodes[-1][:2]


class Battery(object):

    def __init__(self):
        car = IO.load_problem_file()['car']
        self._total_energy = car['battery']  # kW·h
        self._total_energy *= 3.6 * 10 ** 6  # Joule
        self._charge = self._total_energy    # Joule
        self._critical = 0.20  # percentage

        energy = car['ccs_charge']['percentage']
        if energy > 1 and energy <= 100:
            # normalize energy variable
            energy /= 100
        elif not (energy > 0 and energy <= 1):
            raise ValueError('Bad percentage in car ccs_charge')
        energy *= self._total_energy  # car['ccs_charge']['%'] in Joule

        time = car['ccs_charge']['time'] * 60  # from hours to minutes
        self._charge_rate = energy / time  # Joule / minute

    @property
    def charge(self):
        """Energy available in Joule."""
        return self._charge

    @charge.setter
    def x(self, new_energy):
        """Modify charge value."""
        if new_energy <= self._critical * self._total_energy:
            raise BatteryCriticalException()
        self._charge = min(self._total_energy, new_energy)

    def recharge_until(self, asked_energy):
        """Return time (min) to charge battery until asked energy is available.

           Raises InsufficientBatteryException.
        """
        if asked_energy <= 0:
            return 0
        elif asked_energy > (1 - self._critical) * self._total_energy + 1e4:
            raise InsufficientBatteryException()
        self.charge += asked_energy
        return asked_energy / self._charge_rate

    def recharge(self, percentage=0.8):
        """Return time (min) to charge until % of total energy is available.

           Raises InsufficientBatteryException, ValueError.
        """
        if percentage <= self._critical or percentage > 1 + 1e-6:
            raise ValueError(f'Out of bound percentage level ({percentage})')
        asked_energy = self._total_energy * percentage - self._charge
        return self.recharge_until(asked_energy)

    def time_elapsed(self, energy_1, energy_2):
        """Return time (min) to charge from energy_1 to energy_2.

           Raises ValueError.

           Note: internal state of battery is not changed.
        """
        for e in (energy_1, energy_2):
            if e <= 1e-6 or e >= self._total_energy + 1e-6:
                raise ValueError('Energy argument out of battery bounds')

        if energy_1 >= energy_2:
            return 0
        else:
            return (energy_2 - energy_1) / self._charge_rate


class UnfeasibleRouteException(Exception):
    """Route does not satisfy problem constraints."""
    pass


class BatteryCriticalException(UnfeasibleRouteException):
    """Battery reached critical percentage threshold."""
    pass


class InsufficientBatteryException(UnfeasibleRouteException):
    """Battery capacity is not enough to satisfy requested amount of energy."""
    pass
