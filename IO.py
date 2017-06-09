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

import errno
import logging
import networkx as nx
import os
import yaml

import utility

__authors__ = "Serena Ziviani, Federico Motta"
__copyright__ = "E-VRP  Copyright (C)  2017"
__license__ = "GPL3"


def check_workspace():
    """Ensure workspace exist and it contains only necessary files.

       Otherwise it could raise:
           - FileExistsError
           - FileNotFoundError
           - NameError
           - TypeError
    """
    ws = utility.CLI.args().workspace
    if not os.path.isdir(ws):
        raise FileNotFoundError(errno.ENOENT, f'Directory {ws} not found'
                                '\n          Please set a correct workspace')

    if not os.path.isfile(os.path.join(ws, 'edges.shp')):
        raise FileNotFoundError(errno.ENOENT, 'edges.shp not found in '
                                f'workspace ({ws})')

    if not os.path.isfile(os.path.join(ws, 'nodes.shp')):
        raise FileNotFoundError(errno.ENOENT, 'nodes.shp not found in '
                                f'workspace ({ws})')

    graph_read = nx.read_shp(path=os.path.join(ws, 'nodes.shp'), simplify=True)

    # check each node has an altitude attribute
    altitude = utility.CLI.args().altitude
    for node, data in graph_read.nodes_iter(data=True):
        if altitude not in data:
            raise NameError(f'Could not find \'{altitude}\' attribute in '
                            'nodes.shp')

        # check each altitude attribute is a floating point number
        if not isinstance(data[altitude], float):
            raise TypeError('Altitude of node lat: {}, lon {} is not a '
                            'float'.format(*node))

    for f in os.listdir(ws):
        if f not in [prefix + suffix
                     for prefix in ('nodes.', 'edges.')
                     for suffix in ('dbf', 'shp', 'shx')]:
            raise FileExistsError(errno.EEXIST, 'Please remove '
                                  '\'{}\''.format(os.path.join(ws, f)))


def export_problem_to_directory(exit_on_success=False):
    """Populate directory with a shapefile representation of the problem.

       Raises FileNotFoundError
    """
    export_dir = utility.CLI.args().export_dir
    problem_file = utility.CLI.args().problem_file

    if not os.path.isfile(problem_file):
        raise FileNotFoundError(errno.ENOENT, 'Problem file not found '
                                f'({problem_file})')
    problem = load_yaml_file(problem_file)

    if not os.path.isdir(export_dir):
        os.makedirs(export_dir)

    temp_graph = nx.DiGraph()
    temp_graph.add_node((problem['depot'][0]['latitude'],
                         problem['depot'][0]['longitude']))
    nx.write_shp(temp_graph, os.path.join(export_dir, 'depot.shp'))

    for node_type in ('customers', 'stations'):
        temp_graph = nx.DiGraph()
        for node in problem[node_type]:
            temp_graph.add_node((node['latitude'],
                                 node['longitude']))
        nx.write_shp(temp_graph, os.path.join(export_dir, node_type + '.shp'))

    for ext in ('dbf', 'shp', 'shx'):
        os.remove(os.path.join(export_dir, 'edges.' + ext))

    Log.info(f'Exported correctly to \'{export_dir}\' '
             'depot.shp, customers.shp and stations.shp\n')
    if exit_on_success:
        raise SystemExit(0)


def import_shapefile_to_workspace(exit_on_success=False):
    """Populate workspace with translation of import_shapefile into a graph.

       Raises NameError
    """
    import_file = utility.CLI.args().import_file
    ws = utility.CLI.args().workspace

    imported_graph = nx.read_shp(path=import_file, simplify=True)
    Log.info('File \'{}\' imported correctly'.format(import_file))

    if not ws:
        raise NameError('Please set workspace dir')

    nx.write_shp(imported_graph, ws)
    Log.info(f'Exported correctly to \'{ws}\' nodes.shp and edges.shp\n')
    Log.info('PLEASE ADD TO \'{}\' ELEVATION '
             'INFORMATION !'.format(os.path.join(ws, 'nodes.shp')))
    if exit_on_success:
        raise SystemExit(0)


def load_yaml_file(path):
    with open(path, 'r') as f:
        return yaml.load(f)


class Log(object):

    __default = 'critical' if utility.CLI.args().quiet >= 3 else \
                'error' if utility.CLI.args().quiet == 2 else \
                'warning' if utility.CLI.args().quiet == 1 else \
                'debug' if utility.CLI.args().verbose else \
                'info'
    __initialized = False
    __name = 'E-VRP'

    def __log(msg='', data=None, level=None):
        """Print log message if above threshold."""
        if level is None:
            level = Log.__default

        if not Log.__initialized:
            logging_level = getattr(logging, Log.__default.upper())
            logging.basicConfig(format='[%(levelname)-8s] %(message)s',
                                level=logging_level)
            for l in logging.Logger.manager.loggerDict.keys():
                # logging of everything
                logging.getLogger(l).setLevel(logging.INFO)

            # current script / package logging
            logging.getLogger(Log.__name).setLevel(logging_level)
            Log.__initialized = True

        logger = getattr(logging.getLogger(Log.__name), level)
        my_new_line = '\n[{:<8}]     '.format(level.upper())
        if data is None:
            logger(msg.replace('\n', my_new_line))
        else:
            data = yaml.dump(data, default_flow_style=False)
            data = data.replace('\n...', '').rstrip('\n')
            logger(msg.rstrip('\n') + my_new_line +
                   data.replace('\n', my_new_line))

    def critical(msg='', data=None):
        return Log.__log(msg=msg, data=data, level='critical')

    def debug(msg='', data=None):
        return Log.__log(msg=msg, data=data, level='debug')

    def error(msg='', data=None):
        return Log.__log(msg=msg, data=data, level='error')

    def info(msg='', data=None):
        return Log.__log(msg=msg, data=data, level='info')

    def set_level(level):
        if not isinstance(level, str):
            Log.error('Log.set_level() takes a string as argumenent, not a '
                      '{}'.format(type(level)))
            return
        if level not in ('critical', 'debug', 'error', 'info', 'warning'):
            Log.error('Bad level ({}) in Log.set_level()'.format(level))
            return
        Log.__default = level
        Log.__initialized = False

    def warning(msg='', data=None):
        return Log.__log(msg=msg, data=data, level='warning')


# ------------------------------ SCRIPT LOADED ------------------------------ #
if __name__ == '__main__':
    Log.warning('Please do not run that script, load it!')
    exit(1)
