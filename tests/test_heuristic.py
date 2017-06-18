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
import math

from context import solution
from context import heuristic
from context import graph


class test_greedy_heuristic(unittest.TestCase):

    depot = {'lat': 48, 'lon': 16, 'alt': 0, 'type': 'depot'}
    customers = [{'lat': 47, 'lon': 15, 'alt': 1, 'type': 'customer'},
                 {'lat': 49, 'lon': 13, 'alt': 0, 'type': 'customer'},
                 {'lat': 50, 'lon': 14, 'alt': -3, 'type': 'customer'}]
    stations = [{'lat': 48, 'lon': 14, 'alt': 3, 'type': 'station'},
                {'lat': 47, 'lon': 16, 'alt': 2, 'type': 'station'}]
    other_nodes = [{'lat': 49, 'lon': 15, 'alt': 2, 'type': ''},
                   {'lat': 50, 'lon': 16, 'alt': -4, 'type': ''}]

    edges = [{'src_lat': 48, 'src_lon': 16, 'dst_lat': 50, 'dst_lon': 16,
              'speed': 70, 'oneway': False},
             {'src_lat': 50, 'src_lon': 16, 'dst_lat': 50, 'dst_lon': 14,
              'speed': 70, 'oneway': False},
             {'src_lat': 50, 'src_lon': 14, 'dst_lat': 49, 'dst_lon': 15,
              'speed': 30, 'oneway': True},
             {'src_lat': 49, 'src_lon': 15, 'dst_lat': 48, 'dst_lon': 14,
              'speed': 30, 'oneway': True},
             {'src_lat': 48, 'src_lon': 14, 'dst_lat': 49, 'dst_lon': 13,
              'speed': 50, 'oneway': False},
             {'src_lat': 49, 'src_lon': 13, 'dst_lat': 50, 'dst_lon': 14,
              'speed': 50, 'oneway': True},
             {'src_lat': 48, 'src_lon': 14, 'dst_lat': 50, 'dst_lon': 14,
              'speed': 30, 'oneway': True},
             {'src_lat': 48, 'src_lon': 16, 'dst_lat': 49, 'dst_lon': 15,
              'speed': 50, 'oneway': True},
             {'src_lat': 48, 'src_lon': 16, 'dst_lat': 48, 'dst_lon': 14,
              'speed': 30, 'oneway': False},
             {'src_lat': 48, 'src_lon': 14, 'dst_lat': 47, 'dst_lon': 15,
              'speed': 90, 'oneway': False},
             {'src_lat': 47, 'src_lon': 15, 'dst_lat': 47, 'dst_lon': 16,
              'speed': 50, 'oneway': False},
             {'src_lat': 47, 'src_lon': 16, 'dst_lat': 48, 'dst_lon': 16,
              'speed': 50, 'oneway': False}]

    def setUp(self):
        alt_lab = 'ASTGTM2_de'
        stub_graph = nx.DiGraph(name=graph.Graph._osm_name)
        l = [self.depot] + self.customers + self.stations + self.other_nodes
        for node in l:
            # coordinates are (longitude, latitude)
            stub_graph.add_node((node['lon'], node['lat']),
                                {alt_lab: node['alt'], 'type': node['type']})

        for idx, e in enumerate(self.edges):
            s = next(n for n in l
                     if n['lat'] == e['src_lat'] and n['lon'] == e['src_lon'])
            d = next(n for n in l
                     if n['lat'] == e['dst_lat'] and n['lon'] == e['dst_lon'])
            length = math.sqrt(math.pow(e['src_lat'] - e['dst_lat'], 2) +
                               math.pow(e['src_lon'] - e['dst_lon'], 2) +
                               math.pow(s['alt'] - d['alt'], 2))

            # coordinates are (longitude, latitude)
            stub_graph.add_edge((e['src_lon'], e['src_lat']),
                                (e['dst_lon'], e['dst_lat']),
                                {'osm_id': idx, 'length': length,
                                 'speed': e['speed'], 'oneway': e['oneway']})

        self.graph = graph.Graph(from_DiGraph=stub_graph)     # the same
        # self.graph has different attributes from stub_graph
        # nodes have: altitude, type, latitude, longitude
        # edges have: osm_id, length, rise, speed, energy, slope, time
        # self.graph nodes have also inverted coordinates (lat, lon)

        self.cache = graph.CachePaths(self.graph)
        self.route = solution.Route(self.cache, greenest=True)
        self.heuristic = heuristic.GreedyHeuristic(self.graph, self.cache)

    def test_creation_of_feasible_route(self):
        self.heuristic.create_feasible_route()

    def test_creation_of_feasible_solution(self):
        sol = self.heuristic.create_feasible_solution()

    def test_max_time_exceeded_one_time(self):
        self.heuristic._temp_route.append((47, 15, 'customer'))
        self.heuristic.handle_max_time_exceeded()

    def test_insufficient_energy_one_time(self):
        self.heuristic._temp_route.append((47, 15, 'customer'))
        self.heuristic.handle_insufficient_energy()


class test_greedy_metaheuristic(unittest.TestCase):

    depot = {'lat': 48, 'lon': 16, 'alt': 0, 'type': 'depot'}
    customers = [{'lat': 47, 'lon': 15, 'alt': 1, 'type': 'customer'},
                 {'lat': 49, 'lon': 13, 'alt': 0, 'type': 'customer'},
                 {'lat': 50, 'lon': 14, 'alt': -3, 'type': 'customer'}]
    stations = [{'lat': 48, 'lon': 14, 'alt': 3, 'type': 'station'},
                {'lat': 47, 'lon': 16, 'alt': 2, 'type': 'station'}]
    other_nodes = [{'lat': 49, 'lon': 15, 'alt': 2, 'type': ''},
                   {'lat': 50, 'lon': 16, 'alt': -4, 'type': ''}]

    edges = [{'src_lat': 48, 'src_lon': 16, 'dst_lat': 50, 'dst_lon': 16,
              'speed': 70, 'oneway': False},
             {'src_lat': 50, 'src_lon': 16, 'dst_lat': 50, 'dst_lon': 14,
              'speed': 70, 'oneway': False},
             {'src_lat': 50, 'src_lon': 14, 'dst_lat': 49, 'dst_lon': 15,
              'speed': 30, 'oneway': True},
             {'src_lat': 49, 'src_lon': 15, 'dst_lat': 48, 'dst_lon': 14,
              'speed': 30, 'oneway': True},
             {'src_lat': 48, 'src_lon': 14, 'dst_lat': 49, 'dst_lon': 13,
              'speed': 50, 'oneway': False},
             {'src_lat': 49, 'src_lon': 13, 'dst_lat': 50, 'dst_lon': 14,
              'speed': 50, 'oneway': True},
             {'src_lat': 48, 'src_lon': 14, 'dst_lat': 50, 'dst_lon': 14,
              'speed': 30, 'oneway': True},
             {'src_lat': 48, 'src_lon': 16, 'dst_lat': 49, 'dst_lon': 15,
              'speed': 50, 'oneway': True},
             {'src_lat': 48, 'src_lon': 16, 'dst_lat': 48, 'dst_lon': 14,
              'speed': 30, 'oneway': False},
             {'src_lat': 48, 'src_lon': 14, 'dst_lat': 47, 'dst_lon': 15,
              'speed': 90, 'oneway': False},
             {'src_lat': 47, 'src_lon': 15, 'dst_lat': 47, 'dst_lon': 16,
              'speed': 50, 'oneway': False},
             {'src_lat': 47, 'src_lon': 16, 'dst_lat': 48, 'dst_lon': 16,
              'speed': 50, 'oneway': False}]

    def setUp(self):
        alt_lab = 'ASTGTM2_de'
        stub_graph = nx.DiGraph(name=graph.Graph._osm_name)
        l = [self.depot] + self.customers + self.stations + self.other_nodes
        for node in l:
            # coordinates are (longitude, latitude)
            stub_graph.add_node((node['lon'], node['lat']),
                                {alt_lab: node['alt'], 'type': node['type']})

        for idx, e in enumerate(self.edges):
            s = next(n for n in l
                     if n['lat'] == e['src_lat'] and n['lon'] == e['src_lon'])
            d = next(n for n in l
                     if n['lat'] == e['dst_lat'] and n['lon'] == e['dst_lon'])
            length = math.sqrt(math.pow(e['src_lat'] - e['dst_lat'], 2) +
                               math.pow(e['src_lon'] - e['dst_lon'], 2) +
                               math.pow(s['alt'] - d['alt'], 2))

            # coordinates are (longitude, latitude)
            stub_graph.add_edge((e['src_lon'], e['src_lat']),
                                (e['dst_lon'], e['dst_lat']),
                                {'osm_id': idx, 'length': length,
                                 'speed': e['speed'], 'oneway': e['oneway']})

        self.graph = graph.Graph(from_DiGraph=stub_graph)     # the same
        # self.graph has different attributes from stub_graph
        # nodes have: altitude, type, latitude, longitude
        # edges have: osm_id, length, rise, speed, energy, slope, time
        # self.graph nodes have also inverted coordinates (lat, lon)

        self.cache = graph.CachePaths(self.graph)
        self.route = solution.Route(self.cache, greenest=True)
        self.heuristic = heuristic.GreedyHeuristic(self.graph, self.cache)

    def test_metaheuristic(self):
        heuristic.metaheuristic(self.heuristic.create_feasible_solution())

if __name__ == '__main__':
    unittest.main(failfast=False)
