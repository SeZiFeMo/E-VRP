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

import math
import matplotlib.pyplot as plt
import networkx as nx
import os
import warnings

import IO
import utility

utility.check_python_version()


def add_slope_to_edge_properties(graph):
    """Compute edges' slope in radians from node distance and altitude."""
    h = utility.CLI.args().altitude
    # from node (x1, y1)
    for x1, y1 in graph.edge:
        # to node (x2, y2)
        for x2, y2 in graph.edge[(x1, y1)]:
            rise = graph.node[(x2, y2)][h] - graph.node[(x1, y1)][h]
            run = math.hypot(x2 - x1, y2 - y1)
            slope = math.atan2(rise, run)
            graph.edge[(x1, y1)][(x2, y2)]['slope'] = slope


def check_workspace():
    """Ensure workspace exist and it contains only necessary files."""
    ws = utility.CLI.args().workspace
    if not os.path.isdir(ws):
        IO.Log.warning('Directory not found ({})'.format(ws))
        IO.Log.warning('Please set a correct workspace')
        exit(1)

    if not os.path.isfile(os.path.join(ws, 'edges.shp')):
        IO.Log.warning('edges.shp not found in workspace ({})'.format(ws))
        exit(1)

    if not os.path.isfile(os.path.join(ws, 'nodes.shp')):
        IO.Log.warning('nodes.shp not found in workspace ({})'.format(ws))
        exit(1)

    graph_read = nx.read_shp(path=os.path.join(ws, 'nodes.shp'), simplify=True)

    # check each node has an altitude attribute
    altitude = utility.CLI.args().altitude
    for lon, lat in graph_read.node:
        if altitude not in graph_read.node[(lon, lat)]:
            IO.Log.warning('Could not find {} attribute in '
                           'nodes.shp'.format(altitude))
            exit(1)

        # check each altitude attribute is a floating point number
        if not isinstance(graph_read.node[(lon, lat)][altitude], float):
            IO.Log.warning('Altitude of node lat: {}, lon {} is not a '
                           'float'.format(lon, lat))
            exit(1)

    for f in os.listdir(ws):
        if f not in [prefix + suffix
                     for prefix in ('nodes.', 'edges.')
                     for suffix in ('dbf', 'shp', 'shx')]:
            IO.Log.warning('Please remove {}'.format(os.path.join(ws, f)))
            exit(1)


def draw(graph):
    """Wrap networkx draw function and suppress its warnings."""
    with warnings.catch_warnings():
        warnings.filterwarnings('ignore', category=UserWarning)
        nx.draw(graph)
    plt.show()


def import_shapefile_to_workspace():
    """Populate workspace with translation of import_shapefile into a graph."""
    import_file = utility.CLI.args().import_file
    ws = utility.CLI.args().workspace

    imported_graph = nx.read_shp(path=import_file, simplify=True)
    IO.Log.info('File {} imported correctly'.format(import_file))

    if not ws:
        IO.Log.warning('Please set workspace dir')
        exit(1)

    nx.write_shp(imported_graph, ws)
    IO.Log.info('Exported correctly to {} nodes.shp and '
                'edges.shp\n'.format(ws))
    IO.Log.info('PLEASE ADD TO {} ELEVATION '
                'INFORMATION !'.format(os.path.join(ws, 'nodes.shp')))
    exit(0)


def print_edge_properties(graph, fclass_whitelist=None, tag_blacklist=None):
    """For each edge matching the whitelist print tags not in the blacklist."""
    if fclass_whitelist is None:
        fclass_whitelist = ('living_street', 'motorway', 'motorway_link',
                            'primary', 'primary_link', 'residential',
                            'secondary', 'tertiary', 'unclassified')
    if tag_blacklist is None:
        tag_blacklist = ('code', 'lastchange', 'layer', 'ete', 'ShpName',
                         'Wkb', 'Wkt', 'Json')

    # from node (x1, y1)
    for x1, y1 in graph.edge:
        # to node (x2, y2)
        for x2, y2 in graph.edge[(x1, y1)]:
            if graph.edge[(x1, y1)][(x2, y2)]['fclass'] in fclass_whitelist:
                print('\nLon: {}, Lat: {}  ~>'
                      '  Lon: {}, Lat {}'.format(x1, y1, x2, y2))
                for tag in sorted(graph.edge[(x1, y1)][(x2, y2)]):
                    if tag not in tag_blacklist:
                        value = graph.edge[(x1, y1)][(x2, y2)][tag]
                        print('{}: {}'.format(tag, value))


# ----------------------------------- MAIN ---------------------------------- #

if utility.CLI.args().import_file:
    import_shapefile_to_workspace()  # <-- it always exits

if utility.CLI.args().workspace is None:
    print('\nFirst of all import a shapefile (-i option) to a workspace '
          'directory (-w option)\n\n'
          'Then run the program specifing the workspace to use '
          '(with -w option)')
    exit(0)

check_workspace()  # <-- it exits if workspace is not compliant

g = nx.read_shp(path=utility.CLI.args().workspace, simplify=True)
add_slope_to_edge_properties(g)
print_edge_properties(g)
