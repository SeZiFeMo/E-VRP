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
import csv
import networkx as nx

import IO

if __name__ == '__main__':
    raise SystemExit('Please do not load that script, run it!')


class Solution(object):
    """A Solution is a list of Routes."""

    def __init__(self, graph, graph_cache):
        self._graph_cache = graph_cache
        self._graph = graph
        self.routes = list()

    def is_feasible(self):
        """Return if all routes are feasibile."""
        return bool(all([route.is_feasible() for route in self.routes])
                    and len(self.missing_customers()) == 0)

    @property
    def energy(self):
        return sum([route.energy for route in self.routes])

    @property
    def time(self):
        return max([route.time for route in self.routes])

    def missing_customers(self):
        """Return set of missing customers."""
        customers_left = set(self._graph.customers)
        for route in self.routes:
            customers_left.difference_update(route.visited_customers())
        IO.Log.debug(f'Customers left: {customers_left}')
        return customers_left

    def create_csv(self, filename):
        """Export solution to csv file."""
        if not filename.endswith('.csv'):
            filename = filename + '.csv'

        no_kind = 'crossroad'

        with open(filename, 'w') as f:
            id_route = 'Route id'
            lat, lon, kind = 'Latitude', 'Longitude', 'Node type'
            charge_time = 'Charge time (minutes)'
            header = [id_route, lat, lon, kind, charge_time]
            csv_file = csv.DictWriter(f, fieldnames=header, dialect='excel')
            csv_file.writeheader()

            for idx, route in enumerate(self.routes):
                prev_batt = Battery()
                for index, path in enumerate(route._paths):
                    if index == 0:
                        node = path.first_node()
                        row = {id_route: idx, lat: node[0], lon: node[1],
                               kind: node[2] if node[2] else no_kind,
                               charge_time: 0.0}
                        csv_file.writerow(row)

                    for node in path._nodes[1:-1]:
                        row = {id_route: idx, lat: node[0], lon: node[1],
                               kind: node[2] if node[2] else no_kind,
                               charge_time: 0.0}
                        csv_file.writerow(row)

                    last_node = path.last_node()
                    last_batt = route._batteries[index]
                    row = {id_route: idx, lat: last_node[0], lon: last_node[1],
                           kind: last_node[2] if last_node[2] else no_kind,
                           charge_time: 0.0}
                    if last_node[2] == 'station':
                        # check if battery was charged in that station
                        energy = prev_batt.charge
                        energy -= path.energy
                        if last_batt.charge > energy:
                            minutes = last_batt.time_elapsed(energy,
                                                             last_batt.charge)
                            row[charge_time] = minutes
                    csv_file.writerow(row)
                    prev_batt = copy.deepcopy(last_batt)

                # add an empty line between routes
                csv_file.writerow({k: '' for k in header})


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

           dest_node is a tuple of three elements: (latitude, longitude, type)

           Example:
           route = [ Path_from_A_to_B, ... Path_from_L_to_M ]
           route.append((lat_N, lon_N, type_N))
           route = [ Path_from_A_to_B, ... Path_from_L_to_M, Path_from_M_to_N ]

           Raises:
           - UnfeasibleRouteException (without modifing current route)
           - ValueError if nor greenest or shortest flags is set
        """
        if self.is_empty():
            src_node, batt = self._graph_cache.graph.depot, Battery()
        else:
            src_node, batt = self.last_node(), copy.copy(self.last_battery())

        if src_node == dest_node:
            return

        path = self.default_path(src_node, dest_node)

        if path.time + sum(p.time for p in self._paths) > self.time_limit:
            raise MaximumTimeException('Time limit exceeded')

        batt.charge -= path.energy  # can raise BatteryCriticalException

        # it's safe to append path to route because it's feasible
        self._paths.append(path)
        self._batteries.append(batt)

        # if a station is reached recharge the battery
        if dest_node[2] == 'station':
            IO.Log.debug(f'Charging battery in station {dest_node}')
            batt.recharge()

    def insert(self, node, pos):
        """Add to route the path to reach the given node in position pos.

           node is a tuple of three elements: (latitude, longitude, type)

           Example:
           route = [ Path_from_A_to_B, ... Path_from_L_to_M ]
           route.insert((lat_N, lon_N, type_N), 1)
           route = [ Path_from_A_to_N, Path_from_N_to_B, ... Path_from_L_to_M ]

           Raises:
           - UnfeasibleRouteException (without modifing current route)
           - ValueError if nor greenest or shortest flags is set or pos < 0
        """
        if pos < 0:
            raise ValueError('Negative positions are not allowed')

        if self.is_empty() or pos >= len(self._paths):
            self.append(node)
            return

        # backup paths and batteries
        path_bkp, batt_bkp = copy.copy(self._paths), copy.copy(self._batteries)

        if node in [path.last_node() for path in self._paths]:
            self.remove(node)

        nodes_to_append = [node] + [p.last_node() for p in self._paths[pos:]]

        # cut paths and batteries
        self._paths, self._batteries = self._paths[:pos], self._batteries[:pos]

        try:
            for n in nodes_to_append:
                self.append(n)
        except UnfeasibleRouteException as e:
            self._paths, self._batteries = path_bkp, batt_bkp
            raise e

    def remove(self, rm_node):
        """Remove the first path ending with rm_node and the next one.

           rm_node is a tuple of three elements: (latitude, longitude, type)

           Example:
           route = [ Path_from_A_to_B, Path_from_B_to_C, ... Path_from_L_to_M ]
           route.remove((lat_B, lon_B, type_B))
           route = [ Path_from_A_to_C, ... Path_from_L_to_M ]

           Raises:
           - UnfeasibleRouteException (without modifing current route)
           - ValueError if nor greenest or shortest flags is set
        """
        if self.is_empty():
            return

        try:
            idx = next(index for index, path in enumerate(self._paths)
                       if path.last_node() == rm_node)
        except StopIteration:
            # rm_node not found in self._paths
            return

        nodes_to_append = [p.last_node() for p in self._paths[idx + 1:]]

        # backup and cut paths and batteries
        path_bkp, batt_bkp = copy.copy(self._paths), copy.copy(self._batteries)
        self._paths, self._batteries = self._paths[:idx], self._batteries[:idx]

        try:
            for node in nodes_to_append:
                self.append(node)
        except UnfeasibleRouteException as e:
            self._paths, self._batteries = path_bkp, batt_bkp
            raise e

    def substitute(self, old_node, new_node):
        """Substitute the first path ending with old_node and the next one.

           old_node and new_node are tuples of three elements: (lat, lon, type)

           Example:
           route = [ Path_from_A_to_B, Path_from_B_to_C, ... Path_from_L_to_M ]
           route.substitute((lat_B, lon_B, type_B), (lat_S, lon_S, type_S))
           route = [ Path_from_A_to_S, Path_from_S_to_C, ... Path_from_L_to_M ]

           Raises:
           - UnfeasibleRouteException (without modifing current route)
           - ValueError if new_node is already in route
        """
        if self.is_empty():
            return

        try:
            idx = next(index for index, path in enumerate(self._paths)
                       if path.last_node() == old_node)
        except StopIteration:
            # old_node not found in self._paths
            return

        nodes_to_append = [p.last_node() for p in self._paths[idx + 1:]]
        if new_node in nodes_to_append:
            raise ValueError('Could not substitute node with another one '
                             'already in route')

        # backup and cut paths and batteries
        path_bkp, batt_bkp = copy.copy(self._paths), copy.copy(self._batteries)
        self._paths, self._batteries = self._paths[:idx], self._batteries[:idx]

        try:
            self.append(new_node)
            for node in nodes_to_append:
                self.append(node)
        except UnfeasibleRouteException as e:
            self._paths, self._batteries = path_bkp, batt_bkp
            raise e

    def swap(self, node1, node2):
        """Swap the two given nodes.

           node1 and node2 are tuples of three elements: (lat, lon, type)

           Example:
           route = [ Path_A_B, Path_from_B_C, ... Path_L_M, Path_M_N, ... ]
           route.substitute((lat_B, lon_B, type_B), (lat_M, lon_M, type_M))
           route = [ Path_A_M, Path_from_M_C, ... Path_L_B, Path_B_N, ... ]

           Raises:
           - UnfeasibleRouteException (without modifing current route)
        """
        if self.is_empty() or node1 == node2:
            return

        try:
            id1 = next(index for index, path in enumerate(self._paths)
                       if path.last_node() == node1)
            id2 = next(index for index, path in enumerate(self._paths)
                       if path.last_node() == node2)
        except StopIteration:
            # node1 or node2 not found in self._paths
            return

        if id2 < id1:
            id1, id2 = id2, id1
            node1, node2 = node2, node1

        nodes_to_append = [node2]
        nodes_to_append += [p.last_node() for p in self._paths[id1 + 1:id2]]
        nodes_to_append += [node1]
        nodes_to_append += [p.last_node() for p in self._paths[id2 + 1:]]

        # backup and cut paths and batteries
        path_bkp, batt_bkp = copy.copy(self._paths), copy.copy(self._batteries)
        self._paths, self._batteries = self._paths[:id1], self._batteries[:id1]

        try:
            for n in nodes_to_append:
                self.append(n)
        except UnfeasibleRouteException as e:
            self._paths, self._batteries = path_bkp, batt_bkp
            raise e

    @property
    def energy(self):
        return sum([path.energy for path in self._paths])

    @property
    def time(self):
        return sum([path.time for path in self._paths])

    def is_empty(self):
        """Return if path and batteries list are empty.

           Raises IndexError if the two lists have different lengths.
        """
        if len(self._paths) != len(self._batteries):
            raise IndexError('Lengths of paths and batteries lists differ '
                             f'({len(self._paths)} != {len(self._batteries)})')
        return (not self._paths) and (not self._batteries)

    def is_feasible(self, paths=None, batteries=None):
        """Return if feasibility check is passed.

           paths:     list of Path
           batteries: list of Battery

           Raises ValueError if only one argument is set
        """
        # if missing both arguments apply over self ones
        if paths is None and batteries is None:
            IO.Log.debug('solution.is_feasible() applyed over self')
            paths = copy.copy(self._paths)
            batteries = copy.copy(self._batteries)
        elif paths is not None and batteries is not None:
            IO.Log.debug('solution.is_feasible() applyed over given args')
        else:
            raise ValueError('Please set either both or none of the arguments '
                             'in solution.is_feasible() method')

        time_test = 0
        b_test = Battery()
        for i, p in enumerate(paths[:-1]):
            src, dest = p.last_node(), paths[i + 1].last_node()
            try:
                path = self.default_path(src, dest)
                b_test.charge -= path.energy
            except UnfeasibleRouteException as e:
                IO.Log.debug('Caught UnfeasibleRouteException in '
                             f'route.is_feasible() ({str(e)})')
                return False

            time_test += path.time

            # if energy sum is not zero a charge might have happened
            e_sum = batteries[i + 1].charge - batteries[i].charge + path.energy
            if abs(e_sum) > 0 and dest[2] == 'station':
                try:
                    time_test += b_test.recharge_until(batteries[i + 1].charge)
                except UnfeasibleRouteException as e:
                    IO.Log.debug('Caught UnfeasibleRouteException in '
                                 f'route.is_feasible() ({str(e)})')
                    return False
            elif abs(e_sum) > 0.001:
                IO.Log.debug('Trying to charge battery of {abs(e_sum):.1} J '
                             'in a node which is not a station (in '
                             'route.is_feasible())')
                return False

            if time_test > self.time_limit:
                IO.Log.debug('Time limit exceeded of '
                             f'{self.time_limit - time_test} s in '
                             'route.is_feasible()')
                return False
        return True

    def visited_customers(self):
        """Return set of visited customers (lat, lon, 'customer')."""
        return {path.last_node() for path in self._paths
                if path.last_node()[2] == 'customer'}

    def last_battery(self):
        """Return battery status at last reached node.

           None is returned on empty route.
        """
        if not self.is_empty():
            return self._batteries[-1]

    def last_node(self):
        """Return (latitude, longitude, type) of last reached node.

           None is returned on empty route.
        """
        if not self.is_empty():
            return self._paths[-1].last_node()

    def default_path(self, src_node, dest_node):
        """Return greenest or shortest path between src and dest.

           src_node and dest_node are tuples of three elements (lat, lon, type)

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
        except nx.exception.NetworkXNoPath as e:
            raise UnfeasibleRouteException(str(e))


class Path(object):
    """A path is a sequence of nodes visited in a given order.

       A node is a tuple of three elements: (latitude, longitude, type)
    """

    def __init__(self, graph, coor_list=None):
        """Initialize a path from a list of coordinates (lat, lon)."""
        self._graph = graph
        self._nodes = list()  # each item will be a tuple: ( lat, long, type )
        self._saved = dict()  # empty cache for energy, length and time values

        if coor_list is not None:
            for lat, lon, *__ in coor_list:
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
        """Insert node in last position of the node list.

           node_type argument is ignored and overwritten
        """
        node_type = self._graph.node[(node_latitude, node_longitude)]['type']
        self._saved = dict()  # invalidate cached properties
        self._nodes.append((node_latitude, node_longitude, node_type))

    def remove(self, node_latitude, node_longitude, node_type=None):
        """Remove from node list the first occurrence of the specified node.

           node_type argument is ignored, the match is over coordinates.
        """
        for index, (lat, lon, _) in enumerate(self._nodes):
            if (lat, lon) == (node_latitude, node_longitude):
                self._saved = dict()  # invalidate cached properties
                del self._nodes[index]
                return index

    def substitute(self, old_node, new_node):
        """Replace the first occurrence of the old node with new_node.

           old_node and new_node should be tuples of at least two elements.
        """
        for index, (lat, lon, _) in enumerate(self._nodes):
            if (lat, lon) == old_node[:2]:
                self._saved = dict()  # invalidate cached properties
                rec = (*new_node[:2], self._graph.node[new_node[:2]]['type'])
                self._nodes[index] = rec
                return index

    def first_node(self):
        """Raises IndexError if path is empty."""
        if not self._nodes:
            raise IndexError('Could not get first node from empty path')
        return self._nodes[0]

    def last_node(self):
        """Raises IndexError if path is empty."""
        if not self._nodes:
            raise IndexError('Could not get last node from empty path')
        return self._nodes[-1]


class Battery(object):

    def __init__(self):
        """Raises ValueError on malformed ccs_charge percentage in problem."""
        car = IO.load_problem_file()['car'][1]
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
    def charge(self, new_energy):
        """Raises BatteryCriticalException if under threshold."""
        if new_energy <= self._critical * self._total_energy:
            raise BatteryCriticalException('Battery critical')
        self._charge = min(self._total_energy, new_energy)

    def recharge_until(self, asked_energy):
        """Return time (min) to charge battery until asked energy is available.

           Raises InsufficientBatteryException.
        """
        if asked_energy <= 0:
            return 0
        elif asked_energy > (1 - self._critical) * self._total_energy + 1e4:
            raise InsufficientBatteryException('Battery capacity is not '
                                               'enough to satisfy requested '
                                               'amount of energy')
        IO.Log.debug(f'Battery energy before charge: {self.charge}')
        self.charge += asked_energy
        IO.Log.debug(f'Battery energy after charge: {self.charge}')
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

           Raises ValueError on arguments out of bounds.

           Note: internal state of battery is not changed.
        """
        for e in (energy_1, energy_2):
            if e <= 1e-6 or e >= self._total_energy + 1e-6:
                raise ValueError('Energy argument out of battery bounds')

        if energy_1 >= energy_2:
            return 0.0
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


class MaximumTimeException(UnfeasibleRouteException):
    """Route time exceeds the maximum time for a route completion."""
    pass
