#!/usr/bin/env python3
# coding: utf-8

import IO
import matplotlib.pyplot as plt
import networkx as nx
import utility

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

plt.figure()
Graph = nx.read_shp(path=utility.CLI.args().input_file, simplify=True)
nx.draw(Graph)
plt.show()
nx.write_shp(Graph, 'output_test')

# IO.Log.info('EDGES', [d for e in nx.read_shp(utility.CLI.args().input_file).edge.values() for d in e.values()])
