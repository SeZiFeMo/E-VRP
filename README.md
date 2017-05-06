# E-VRP
E-VRP is a project about the routing of a fleet of electrical vehicles.

E-VRP is a project developed for the Application of Operational Research exam
at University of Modena and Reggio Emilia.

# Usage
```
graph.py [-h] [-i file] [-q | -v]

optional arguments:
  -h, --help           show this help message and exit
  -i file.shp, --input file.shp
                       Shapefile to build initial graph
  -q, --quiet          Set logging to WARNING, ERROR or CRITICAL (-q|-qq|-qqq)
  -v, --verbose        Set logging to DEBUG (default level is INFO)
```
# License

E-VPR Copyright (C) 2017 Serena Ziviani, Federico Motta

This program comes with ABSOLUTELY NO WARRANTY.

This is free software, and you are welcome to redistribute it under certain
conditions; read [LICENSE](https://github.com/sere/E-VRP/blob/master/LICENSE)
file for details.

# Requirements
* [Python 3](https://www.python.org) (>= 3.6)
* [Matplotlib](https://matplotlib.org)
* [Networkx](https://networkx.github.io)
* [PyYAML](http://pyyaml.org/wiki/PyYAML)
