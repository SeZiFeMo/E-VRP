# E-VRP
E-VRP is a project about the routing of a fleet of electrical vehicles.

E-VRP is a project developed for the Application of Operational Research exam
at University of Modena and Reggio Emilia.

# Usage
```
e-vrp.py [-h] [-3] [-a tag] [-c] [-d] [-e dir] [-i file.shp]
                [-s file.yaml] [-t sec] [-q | -v] [-w dir]

E-VRP is a project about the routing of a fleet of electrical vehicles.

optional arguments:
  -h, --help            show this help message and exit
  -3, --3-opt           include 3-opt neighborhood in VNS metaheuristic (can lead to greater computation time). Default=False)
  -a tag, --altitude tag
                        tag describing the elevation of nodes in node.shp (default=ASTGTM2_de)
  -c, --csv-solution    create csv file with solution (default=False)
  -d, --draw-svg        generate svg images of both heuristic and metaheuristic solutions (default=False)
  -e dir, --export dir  export to directory a shapefile representation of the problem to solve
  -i file.shp, --import file.shp
                        import shapefile to workspace
  -s file.yaml, --solve file.yaml
                        solve the problem described in file (default=problem.yaml)
  -t sec, --time sec    VNS time limit (maximum seconds of computation (default=60)
  -q, --quiet           set logging to WARNING, ERROR or CRITICAL (-q|-qq|-qqq)
  -v, --verbose         set logging to DEBUG (default level is INFO)
  -w dir, --workspace dir
                        directory with edges.shp and node.shp (with elevation information)
```

Currently, E-VRP works in two stages: a preparatory stage where one can import a shapefile and add the altitude informations (the informations from this stage are saved in a specific folder called _workspace_ and a working stage where E-VRP solves the optimization problem on a workspace).

## If you need to create a workspace

The relevant options for this stage are:
* ```-a tag, --altitude tag```
* ```-e dir, --export dir```
* ```-i file.shp, --import```
* ```-q, --quiet``` and ```-v, --verbose```
* ```-w dir, --workspace dir```

1. create a workspace:
 ```./e-vrp.py -i shapefile_folder -w workspace_folder```

2. add elevation information to workspace_folder/nodes.shp using your preferred GIS tool
 For example, with QGIS you have to open workspace_folder/node.shp and a dem.tif, then use the _Point Sampling Tool Plugin_ to create a new node.shp

3. run the program specifying the workspace created:
 ```./e-vrp.py -w workspace_folder```

## If you already have a workspace
All options except for ```-e dir, --export dir``` and ```-i file.shp, --import``` can be used in this stage.

### Examples

```./e-vrp.py -w workspace```
This solves the problem in ```problem.yaml```, stopping the computation after a maximum of 60 seconds.

```./e-vrp.py -w workspace -t 600```
Solve ```problem.yaml``` within a maximum of ten minutes

```./e-vrp.py -w workspace -t 600 -d```
Solve ```problem.yaml``` within a maximum of ten minutes and generate svg images of both heuristic and metaheuristic solutions

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
