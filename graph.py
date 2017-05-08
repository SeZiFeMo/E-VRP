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

# -------------------------------- SCRIPT RUN ------------------------------- #
if __name__ != '__main__':
    print('Please do not load that script, run it!')
    exit(1)

# Add to the following loop every external library used!
for lib in ('matplotlib.pyplot as plt', 'networkx as n', 'yaml'):
    try:
        exec('import ' + str(lib))
    except ImportError:
        print('Could not import {} library, please install it!'.format(lib))
        exit(1)

import matplotlib.pyplot as plt
import networkx as nx
import warnings

import IO
import utility

utility.check_python_version()

graph = nx.read_shp(path=utility.CLI.args().input_file, simplify=True)
IO.Log.info("Type of graph: " + str(type(graph)))

with warnings.catch_warnings():
    warnings.filterwarnings("ignore", category=UserWarning)
#    nx.draw(graph)
# plt.show()

for from_lon, from_lat in graph.edge:
    for to_lon, to_lat in graph.edge[(from_lon, from_lat)]:
        if graph.edge[(from_lon, from_lat)][(to_lon, to_lat)]['fclass'] \
           in ('living_street', 'motorway', 'motorway_link', 'primary',
               'primary_link', 'residential', 'secondary', 'tertiary',
               'unclassified'):
            print("\nFROM LON: {}, LAT: {}\tTO LON: {}, LAT {}".format(
                    from_lon, from_lat, to_lon, to_lat))
            for tag in graph.edge[(from_lon, from_lat)][(to_lon, to_lat)]:
                if tag not in ('lastchange', 'ShpName', 'Wkb', 'Wkt', 'Json'):
                    print(tag + ': ' + repr(graph.edge[(from_lon,
                                                    from_lat)][(to_lon,
                                                                to_lat)][tag]))

# nx.write_shp(graph, 'output_test')
