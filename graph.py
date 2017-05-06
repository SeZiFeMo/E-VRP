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

import matplotlib.pyplot as plt
import networkx as nx
import warnings

import IO
import utility

__authors__ = "Serena Ziviani, Federico Motta"
__copyright__ = "E-VRP  Copyright (C)  2017"
__license__ = "GPL3"

# -------------------------------- SCRIPT RUN ------------------------------- #
if __name__ != '__main__':
    IO.Log.warning('Please do not load that script, run it!')
    exit(1)


utility.check_python_version()

# Add to the following loop every external library used!
for lib in ('matplotlib.pyplot as plt', 'networkx as n', 'yaml'):
    try:
        exec('import ' + str(lib))
    except ImportError:
        IO.warning('Could not import {} library, '
                   'please install it!'.format(lib))
        exit(1)

Graph = nx.read_shp(path=utility.CLI.args().input_file, simplify=True)
with warnings.catch_warnings():
    warnings.filterwarnings("ignore", category=UserWarning)
    nx.draw(Graph)
plt.show()
nx.write_shp(Graph, 'output_test')

# IO.Log.info('EDGES', [d for e in nx.read_shp(utility.CLI.args().input_file).edge.values() for d in e.values()])
