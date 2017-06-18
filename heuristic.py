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
import time
import copy

import IO
import solution
import utility


class GreedyHeuristic(object):

    def __init__(self, abstract_g, cache):
        self._abstract_g = abstract_g
        self._cache = cache
        self._depot = abstract_g.depot
        self._temp_route = solution.Route(self._cache, greenest=True)
        self._customer = [(*coor, data['type'])
                          for coor, data in abstract_g.nodes_iter(data=True)
                          if data['type'] == 'customer']

        assert self._depot is not None, 'Could not find depot in graph'

    def create_feasible_solution(self):
        """Build a feasible, greedy solution for the problem."""
        sol = solution.Solution(self._abstract_g, self._cache)
        # While customers are not all served:
        while len(self._customer) > 0:
            self.create_feasible_route()
            sol.routes.append(self._temp_route)
        return sol

    def create_feasible_route(self):
        current_node = self._depot
        while True:
            if len(self._customer) == 0:
                # We have visited all customers: add depot
                dest = self._depot
            else:
                dest = self.find_nearest(current_node, 'customer')
            try:
                self._temp_route.append(dest)
            except solution.BatteryCriticalException:
                IO.Log.warning(f'Inserting node {dest} makes'
                               ' the battery below critical threshold')
                self.handle_insufficient_energy(self._temp_route)
            except solution.MaximumTimeException:
                IO.Log.warning(f'Inserting node {dest} makes self._temp_route'
                               ' exceed the maximum time')
                self.handle_max_time_exceeded(self._temp_route)
                return
            else:
                IO.Log.debug(f'Successfully inserted node {dest}')
                try:
                    self._customer.remove(dest)
                except ValueError as e:
                    if dest == self._depot and len(self._customer) == 0:
                        return
                    else:
                        raise e
                current_node = dest

    def handle_max_time_exceeded(self):
        # TODO change greenest to shortest before attempting to return to depot
        try:
            self._temp_route.append(self._depot)
        except solution.MaximumTimeException:
            IO.Log.debug('Inserting depot still raises a MaximumTimeException')
            last = self._temp_route.last_node()
            if last is None:
                raise SystemExit(f'Max time {self._temp_route.time_limit} too '
                                 'short for this problem!')
            else:
                self._temp_route.remove(last)
            self.handle_max_time_exceeded(self._temp_route)

    def handle_insufficient_energy(self):
        dest = self.find_nearest(self._temp_route.last_node(), 'station')
        try:
            self._temp_route.append(dest)
        except solution.BatteryCriticalException:
            IO.Log.debug('Inserting nearest station still raises '
                         'BatteryCriticalException')
            last = self._temp_route.last_node()
            if last is None:
                raise SystemExit('Total battery energy '
                                 F'{solution.Battery().charge} is too small '
                                 'for this problem!')
            else:
                self._temp_route.remove(last)
            self.handle_insufficient_energy(self._temp_route)

    def find_nearest(self, current_node, type_to_find):
        min_time = math.inf
        min_node = None
        for dest, green, short in self._cache.source_iterator(current_node):
            if type_to_find == 'customer':
                if dest[2] == type_to_find and \
                   dest in self._customer and \
                   green.time < min_time:
                    min_time = green.time
                    min_node = dest
            else:
                if dest[2] == type_to_find and green.time < min_time:
                    min_time = green.time
                    min_node = dest
        return min_node


def two_opt_neighbors(sol):
    """Generator which produces a series of solutions close to the given one.

       (close in neighborhood sense)

       note: https://docs.python.org/3/glossary.html#term-generator
             https://en.wikipedia.org/wiki/2-opt
              ~> A   C              ~> A - C
                   X ↑    becomes          ↓
              <~ D   B              <~ D - B
              (A, B, C, D)          (A, C, B, D)
    """
    my_sol = copy.deepcopy(sol)
    for route in my_sol.routes:
        i = 0
        while i < len(route._paths) - 2:                          # example:
            node_i = route._paths[i].last_node()                  # B
            node_j = route._paths[i + 1].last_node()              # C
            tail = [p.last_node() for p in route._paths[i + 2:]]  # D
            # remove B, C, D
            for node in [node_i, node_j] + tail:
                try:
                    route.remove(node)
                except solution.UnfeasibleRouteException as e:
                    IO.Log.debug('Unexpected UnfeasibleRouteException while '
                                 'removing last node from a route! '
                                 f'({str(e)})')
                    break
            else:
                # append C, B, D
                for node in [node_j, node_i] + tail:
                    try:
                        route.append(node)
                    except solution.UnfeasibleRouteException as e:
                        IO.Log.debug(f'Iteration {i} in two_opt_neighbors() '
                                     'generator got UnfeasibleRouteException: '
                                     f'{str(e)}')
                        break
                else:
                    yield my_sol
            i += 1


def three_opt_neighbors(sol):
    """Generator which produces a series of solutions close to the given one.

       (close in neighborhood sense)

       note: https://docs.python.org/3/glossary.html#term-generator
             https://en.wikipedia.org/wiki/3-opt
    """
    return iter([])


def move_neighbors(sol):
    """Generator which produces a move neighborhood of the given solution."""
    mod_sol = copy.deepcopy(sol)
    for route in mod_sol.routes:
        for i in range(len(route._paths) - 1):
            node_i = route._paths[i].last_node()
            for j in range(i + 1, len(route._paths)):
                try:
                    route.remove(node_i)  # a remove shifts indexes left by one
                    route.insert(node_i, j - 1)

                    # but a simple swap would achieve the same result !!
                    # (and in a more efficient way)
                    # route.swap(node_i, route._paths[j].last_node()
                except solution.UnfeasibleRouteException as e:
                    IO.Log.debug(f'Move of node {i} ({node_i}) to position '
                                 f'{j} is not feasible ({str(e)})')
                    continue
                else:
                    yield mod_sol


def swap_neighbors(sol):
    """Generator which produces a swap neighborhood of the given solution."""
    mod_sol = copy.deepcopy(sol)
    for route in mod_sol.routes:
        for i in range(len(route._paths) - 1):
            node_i = route._paths[i].last_node()
            for j in range(i + 1, len(route._paths)):
                node_j = route._paths[j].last_node()
                try:
                    route.swap(node_i, node_j)
                except solution.UnfeasibleRouteException as e:
                    IO.Log.debug(f'Swap between node {i} ({node_i}) and '
                                 f'node {j} ({node_j}) is not feasible '
                                 f'({str(e)})')
                    continue
                else:
                    yield mod_sol


neighborhoods = {'2-opt': two_opt_neighbors,
                 'swap': swap_neighbors,
                 'move': move_neighbors}


def metaheuristic(initial_solution, max_iter=10**3):
    """Look (in different initial solution neighborhoods) for better solutions.

       (a first improving approach is used in neighborhood exploration)

       Return the best solution found after max_iter or maximum time exceeded.
    """
    actual_solution = copy.deepcopy(initial_solution)
    vns_it = 0
    best_it = 0
    t0 = time.time()
    num_explored_solutions = 0
    for vns_it in range(max_iter):
        # exit if time exceeded
        if time.time() > t0 + utility.CLI.args().max_time:
            break

        # explore each available neighborhood
        for neighborhood_generator in neighborhoods.values():
            # explore each solution in the neighborhood
            sol = local_search(actual_solution, neighborhood_generator)
            if sol[0] is not None:
                # local search found a better solution in the neighborhood
                actual_solution = sol[0]
                best_it = vns_it
            num_explored_solutions += sol[1]
        if vns_it >= best_it + 3:
            break

    t_tot = time.time() - t0
    IO.Log.info('VNS summary:')
    IO.Log.info(f'{vns_it:>8}     iterations')
    IO.Log.debug(f'({vns_it - best_it - 1:>7}     empty iterations)')
    IO.Log.info(f'{t_tot:>12.3f} seconds')
    IO.Log.info(f'{num_explored_solutions:>8}     explored sol.')
    return actual_solution


def local_search(actual_solution, neighborhood):
    """Look in the neighborhood of actual_solution for better neighbors."""
    num_explored_solutions = 0
    for neighbor in neighborhood(actual_solution):
        num_explored_solutions += 1
        # return the first improving one
        if (neighbor.time < actual_solution.time
            or (neighbor.time == actual_solution.time and
                neighbor.energy < actual_solution.energy)):
            delta_energy = neighbor.energy - actual_solution.energy
            delta_time = neighbor.time - actual_solution.time
            IO.Log.info(f'VNS found a better solution '
                        f'({delta_time:>+10.6f} m, '
                        f'{delta_energy:>+10.1f} J)')
            return copy.deepcopy(neighbor), num_explored_solutions
    # Could not find a better solution in actual_solution's neigborhood
    # => actual_solution is a local optimum for that neighborhood
    return None, num_explored_solutions
