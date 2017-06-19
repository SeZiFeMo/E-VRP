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
        assert self._depot is not None, 'Could not find depot in graph'

    def create_feasible_solution(self):
        """Build a feasible, greedy solution for the problem."""
        sol = solution.Solution(self._abstract_g, self._cache)
        # While customers are not all served:
        while sol.missing_customers():
            self._customer = list(sol.missing_customers())
            self._temp_route = solution.Route(self._cache, greenest=True)
            self.create_feasible_route()
            sol.routes.append(self._temp_route)
        assert not sol.missing_customers(), 'self._customer is empty even ' \
                                            'if sol.missing_customers() is not'
        return sol

    def create_feasible_route(self):
        current_node = self._depot
        while True:
            if not self._customer:
                # We have visited all customers: add depot
                dest = self._depot
            else:
                dest = self.find_nearest(current_node, 'customer')
            try:
                self._temp_route.append(dest)
            except solution.BatteryCriticalException:
                IO.Log.debug(f'Inserting node {dest} makes'
                             ' the battery below critical threshold')
                self.handle_insufficient_energy()
            except solution.MaximumTimeException:
                IO.Log.debug(f'Inserting node {dest} makes self._temp_route'
                             ' exceed the maximum time')
                self.handle_max_time_exceeded()
                return
            except solution.UnfeasibleRouteException as e:
                IO.Log.debug('Caught UnfeasibleRouteException in '
                             'GreedyHeuristic.create_feasible_route() '
                             f'({str(e)})')
            else:
                IO.Log.debug(f'Successfully inserted node {dest}')
                if dest == self._depot:
                    return
                else:
                    self._customer.remove(dest)
                    current_node = dest

    def handle_max_time_exceeded(self):
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
            self.handle_max_time_exceeded()
        else:
            IO.Log.debug(f'Successfully inserted node {self._depot}')

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
            self.handle_insufficient_energy()
        else:
            IO.Log.debug(f'Successfully inserted node {dest}')
            IO.Log.debug(f'Recharging battery in station {dest}')
            self._temp_route.last_battery().recharge()

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
              ~> A   C - ...                ~> A - C - ...
                   X        )    becomes                  )
              <~ D   B - ...                <~ D - B - ...
              (A, B, ... C, D)              (A, C, ..., B, D)
    """
    mod_sol = copy.deepcopy(sol)
    for route in mod_sol.routes:
        for i in utility.shuffled_range(len(route._paths) - 1):
            if i >= len(route._paths):  # should never happen
                continue
            node_i = route._paths[i].last_node()        # node C of the example
            for j in utility.shuffled_range(i + 1, len(route._paths)):
                if j >= len(route._paths):  # should never happen
                    continue
                node_j = route._paths[j].last_node()    # node B of the example
                try:
                    route.swap(node_i, node_j)
                except solution.UnfeasibleRouteException as e:
                    IO.Log.debug(f'two_opt_neighbors() generator got '
                                 f'UnfeasibleRouteException: {str(e)}')
                    continue
                else:
                    yield mod_sol
                finally:
                    mod_sol = copy.deepcopy(sol)


def three_opt_neighbors(sol, _d={}):
    """Generator which produces a series of solutions close to the given one.

       (close in neighborhood sense)

       note: https://docs.python.org/3/glossary.html#term-generator
             https://en.wikipedia.org/wiki/3-opt

       explanation: the three edge are selected by choosing 3 different nodes
                    (each edge will be the one arriving to that node);
                    to try all the possible reconnections of the three selected
                    edges we need to understand which are the possible
                    permutations of them:
        >>> import itertools
        >>> for i, j, k in itertools.permutations('ijk'):
        >>>     print(f'{i}\t{j}\t{k}')
           i    j    k          # actual arrangement (will be skipped)
           i    k    j          # 'i' is in the same position
           j    i    k          # 'k' is in the same position
           j    k    i          # that solution must be explored with 3-opt
           k    i    j          # that solution must be explored with 3-opt
           k    j    i          # 'j' is in the same position

                    In practise the arrangements which keep i, j, and k in the
                    current positions will be skipped because they are already
                    explored by the visit of the 2-opt neighborhood!
    """
    if not utility.CLI.args().use_3_opt_neighborhood:
        if 'written_once' not in _d:
            IO.Log.debug('To explore 3-opt neighborhood use -3 CLI argument.')
            _d['written_once'] = True
        return iter(list())
    mod_sol = copy.deepcopy(sol)
    for route in mod_sol.routes:
        for i in utility.shuffled_range(len(route._paths) - 2):
            if i >= len(route._paths):  # should never happen
                continue
            node_i = route._paths[i].last_node()
            for j in utility.shuffled_range(i + 1, len(route._paths) - 1):
                if j >= len(route._paths):  # should never happen
                    continue
                node_j = route._paths[j].last_node()
                for k in utility.shuffled_range(j + 1, len(route._paths)):
                    if k >= len(route._paths):  # should never happen
                        continue
                    node_k = route._paths[k].last_node()
                    route_bkp = copy.deepcopy(route)        # i - j - k
                    try:
                        route.swap(node_i, node_j)          # j - i - k
                        route.swap(node_i, node_k)          # j - k - i
                    except solution.UnfeasibleRouteException as e:
                        IO.Log.debug(f'three_opt_neighbors() generator got '
                                     f'UnfeasibleRouteException: {str(e)}')
                    else:
                        yield mod_sol
                    mod_sol = copy.deepcopy(sol)
                    route = copy.deepcopy(route_bkp)        # i - j - k
                    try:
                        route.swap(node_i, node_k)          # k - j - i
                        route.swap(node_j, node_i)          # k - i - j
                    except solution.UnfeasibleRouteException as e:
                        IO.Log.debug(f'three_opt_neighbors() generator got '
                                     f'UnfeasibleRouteException: {str(e)}')
                    else:
                        yield mod_sol
                    mod_sol = copy.deepcopy(sol)


def move_neighbors(sol):
    """Generator which produces a move neighborhood of the given solution."""
    mod_sol = copy.deepcopy(sol)
    for route in mod_sol.routes:
        for i in utility.shuffled_range(len(route._paths) - 1):
            if i >= len(route._paths):  # should never happen
                continue
            node_i = route._paths[i].last_node()
            for j in utility.shuffled_range(i + 1, len(route._paths)):
                try:
                    route.remove(node_i)  # a remove shifts indexes left by one
                    route.insert(node_i, j - 1)
                except solution.UnfeasibleRouteException as e:
                    IO.Log.debug(f'Move of node {i} ({node_i}) to position '
                                 f'{j} is not feasible ({str(e)})')
                    continue
                else:
                    yield mod_sol
                finally:
                    mod_sol = copy.deepcopy(sol)


def swap_neighbors(sol):
    """Generator which produces a swap neighborhood of the given solution."""
    mod_sol = copy.deepcopy(sol)
    for a in utility.shuffled_range(len(mod_sol.routes) - 1):
        route_a = mod_sol.routes[a]
        for b in utility.shuffled_range(a + 1, len(mod_sol.routes)):
            route_b = mod_sol.routes[b]
            for i in utility.shuffled_range(len(route_a._paths)):
                if i >= len(route_a._paths):  # should never happen
                    continue
                node_i = route_a._paths[i].last_node()
                for j in utility.shuffled_range(len(route_b._paths)):
                    if j >= len(route_b._paths):  # should never happen
                        continue
                    node_j = route_b._paths[j].last_node()
                    try:
                        route_a.remove(node_i)
                        route_b.remove(node_j)

                        route_a.insert(node_j, i)
                        route_a.insert(node_i, j)
                    except solution.UnfeasibleRouteException as e:
                        IO.Log.debug(f'Swap between node {i} ({node_i}) of '
                                     f'route {a} and node {j} ({node_j}) of '
                                     f'route {b} is not feasible ({str(e)})')
                        continue
                    else:
                        yield mod_sol
                    finally:
                        mod_sol = copy.deepcopy(sol)


neighborhoods = {'2-opt': two_opt_neighbors,
                 '3-opt': three_opt_neighbors,
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
        for k, neighborhood_generator in enumerate(neighborhoods.values()):
            # explore each solution in the neighborhood
            sol = shake(actual_solution, k)
            sol = local_search(sol, neighborhood_generator)
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
            assert not neighbor.missing_customers(), 'There are some ' \
                                                     'customers left out'
            assert neighbor.is_feasible(), 'neighbor found is not feasible'
            return copy.deepcopy(neighbor), num_explored_solutions
    # Could not find a better solution in actual_solution's neigborhood
    # => actual_solution is a local optimum for that neighborhood
    return None, num_explored_solutions

def shake(sol, k):
    """Make k random feasible swap moves on the given solution."""
    for i in range(k):
        try:
            sol = swap_neighbors(sol).__next__()
        except StopIteration:
            IO.Log.debug(f'Stopped after {i} shake iterations')
    return sol
