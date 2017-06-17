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

import solution
import IO


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
        last_node = None  # FIXME unused variable?
        while True:
            dest = self.find_nearest(current_node, 'customer')
            if dest is None:
                # We have visited all customers
                return
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
                IO.Log.debug(f'Successful insert; node {dest}')
                self._customer.remove(dest)
                last_node = current_node  # FIXME unused variable?
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


def two_opt_neighbors(solution):
    """Generator which produces a series of solutions close to the given one.

       (close in neighborhood sense)

       note: https://docs.python.org/3/glossary.html#term-generator
             https://en.wikipedia.org/wiki/2-opt
              ~> A   C              ~> A - C
                   X ↑    becomes          ↓
              <~ D   B              <~ D - B
              (A, B, C, D)          (A, C, B, D)
    """
    for 
    pass


def three_opt():
    pass


def move():
    pass


neighborhoods = {'2-opt': two_opt_neighbors,
                 '3-opt': three_opt,
                 'move': move}


def metaheuristic(abstract_g, cache):
    """Solve the routing problem expressed with abstract_g and cache.

    Uses a first-improvement local search."""
    greedy_heuristic = GreedyHeuristic(abstract_g, cache)
    initial_solution = greedy_heuristic.create_feasible_solution()

    max_iteration = 1000
    it = 0

    for it in range(max_iteration):
        for neigh in neighborhoods:
            x = local_search(initial_solution, neigh)
            if x.time < initial_solution.time:
                initial_solution = x
                break


def local_search(solution, neighborhood):
    """First-improvement search in the given neighborhood."""
    mod_solution = copy.copy(solution)
    return mod_solution
