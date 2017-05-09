# E-VRP
E-VRP is a project about the routing of a fleet of electrical vehicles.

E-VRP is a project developed for the Application of Operational Research exam
at University of Modena and Reggio Emilia.

# Usage
```
graph.py [-h] [-a tag] [-i file.shp] [-q | -v] [-w dir]

optional arguments:
  -h, --help                        show this help message and exit
  -a tag, --altitude tag            tag describing the elevation of nodes in node.shp (default=ASTGTM2_de)
  -i file.shp, --import file.shp    import shapefile to workspace
  -q, --quiet                       set logging to WARNING, ERROR or CRITICAL (-q|-qq|-qqq)
  -v, --verbose                     set logging to DEBUG (default level is INFO)
  -w dir, --workspace dir           directory with edges.shp and node.shp (with elevation information)

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
