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

# Add to the following loop every external library used!
for lib in ('graphviz', 'networkx as nx', 'yaml'):
    try:
        exec('import ' + str(lib))
    except ImportError:
        raise SystemExit(f'Could not import {lib} library, please install it!')

import graph
import heuristic
import IO
import utility

utility.check_python_version()


def main():
    try:
        if utility.CLI.args().import_file:
            IO.import_shapefile_to_workspace(exit_on_success=True)
        elif utility.CLI.args().export_dir:
            IO.export_problem_to_directory(exit_on_success=True)
        elif utility.CLI.args().workspace is None:
            raise utility.UsageException()

        IO.check_workspace()
    except (FileExistsError, FileNotFoundError) as e:
        print(str(e))
        exit(e.errno)
    except (NameError, TypeError, utility.UsageException) as e:
        print(str(e))
        exit(1)

    try:
        osm_g = graph.Graph(osm_shapefile=utility.CLI.args().workspace)
        osm_g.label_nodes()
        osm_g.check_problem_solvability()
        IO.Log.debug('Graph from shapefile passed solvability tests')

        abstract_g = graph.Graph(from_DiGraph=osm_g)
        IO.Log.debug('Created abstract graph')
    except (NameError, RuntimeError, TypeError) as e:
        print(str(e))
        exit(2)

    cache = graph.CachePaths(abstract_g)
    IO.Log.debug('Created cache over abstract graph')

    # create a greedy heuristic solution
    heur = heuristic.GreedyHeuristic(abstract_g, cache)
    initial_sol = heur.create_feasible_solution()
    IO.Log.debug('Greedy solution {} feasible'.format(
                 'is' if initial_sol.is_feasible() else 'not'))
    IO.Log.info('Greedy solution cost        '
                f'  {initial_sol.time:>9.6f} m, {initial_sol.energy:>10.1f} J')

    # find better solutions with metaheuristic
    meta_sol = heuristic.metaheuristic(initial_sol, max_iter=10**6)
    IO.Log.debug('Metaheuristic solution {} feasible'.format(
                 'is' if meta_sol.is_feasible() else 'is not'))
    IO.Log.info('Metaheuristic solution cost '
                f'  {meta_sol.time:>9.6f} m, {meta_sol.energy:>10.1f} J')
    IO.Log.info('Total gain:                 '
                f'({initial_sol.time - meta_sol.time:>+10.6f} m, '
                f'{initial_sol.energy - meta_sol.energy:>+10.1f} J)')

    if utility.CLI.args().csv_solution:
        initial_sol.create_csv('heuristic')
        IO.Log.info('Exported initial solution to heuristic.csv')
        meta_sol.create_csv('metaheuristic')
        IO.Log.info('Exported best solution to metaheuristic.csv')
    else:
        IO.Log.info('To export solution to csv file use -c CLI argument.')

    if utility.CLI.args().draw_svg:
        graph.DrawSVG('heuristic', initial_sol).save()
        IO.Log.info('Created heuristic.svg')
        graph.DrawSVG('metaheuristic', meta_sol).save()
        IO.Log.info('Created metaheuristic.svg')
    else:
        IO.Log.info('To generate svg images of both heuristic and '
                    'metaheuristic')
        IO.Log.info('solutions use -d CLI argument.')


# ----------------------------------- MAIN ---------------------------------- #
if __name__ == '__main__':
    main()
