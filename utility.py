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

import argparse
import sys

__authors__ = "Serena Ziviani, Federico Motta"
__copyright__ = "E-VRP  Copyright (C)  2017"
__license__ = "GPL3"

# ------------------------------ SCRIPT LOADED ------------------------------ #
if __name__ == '__main__':
    raise SystemExit('Please do not run that script, load it!')


def check_python_version():
    if sys.version_info < (3,):
        major, minor, *__ = sys.version_info
        raise SystemExit('You are using the Python interpreter '
                         f'{major}.{minor}.\n'
                         'Please use at least Python version 3!')


def energy(rise, length, consumption, weight, **kwargs):
    """Return energy spent to raise a car (in Joule).

       Rise and length are measured in meters
       consumption in kW⋅h/100km
       weight in kilograms
    """
    length /= 10**3  # m to km
    theta = -2 / 3 if rise < 0 else 1
    consumption *= 36000  # kW⋅h/100km  to  J/km
    return consumption * length + theta * weight * 9.81 * rise


class CLI(object):

    _args = None
    _description = 'E-VRP is a project about the routing of a fleet of '      \
        'electrical vehicles.'
    _epilog = 'E-VRP is a project developed for the Application of '          \
        'Operational Research exam\nat University of Modena and Reggio '      \
        'Emilia.\n\n'                                                         \
        'E-VRP Copyright (C) 2017 Serena Ziviani, Federico Motta\n\n'         \
        'This program comes with ABSOLUTELY NO WARRANTY.\n'                   \
        'This is free software, and you are welcome to redistribute it\n'     \
        'under certain conditions; read LICENSE file for details.\n\n'        \
        'REQUIREMENTS: Python 3 (>= 3.6)\n'                                   \
        '              Matplotlib   https://matplotlib.org\n'                 \
        '              Networkx     https://networkx.github.io\n'             \
        '              PyYAML       http://pyyaml.org/wiki/PyYAML\n'

    def args(self=None):
        if CLI._args is None:
            parser = argparse.ArgumentParser(
                formatter_class=argparse.RawTextHelpFormatter,
                description=CLI._description,
                epilog=CLI._epilog)
            group = parser.add_mutually_exclusive_group()
            parser.add_argument('-a', '--altitude',
                                default='ASTGTM2_de',
                                dest='altitude',
                                help='tag describing the elevation of nodes '
                                     'in node.shp (default=ASTGTM2_de)',
                                metavar='tag',
                                type=str)
            parser.add_argument('-e', '--export',
                                dest='export_dir',
                                help='export to directory a shapefile '
                                     'representation of the problem to solve',
                                metavar='dir',
                                type=str)
            parser.add_argument('-i', '--import',
                                dest='import_file',
                                help='import shapefile to workspace',
                                metavar='file.shp',
                                type=str)
            parser.add_argument('-s', '--solve',
                                default='problem.yaml',
                                dest='problem_file',
                                help='solve the problem described in file '
                                     '(default=problem.yaml)',
                                metavar='file.yaml',
                                type=str)
            group.add_argument('-q', '--quiet',
                               action='count',
                               default=0,
                               help='set logging to WARNING, ERROR or '
                                    'CRITICAL (-q|-qq|-qqq)')
            group.add_argument('-v', '--verbose',
                               action='store_true',
                               help='set logging to DEBUG '
                                    '(default level is INFO)')
            parser.add_argument('-w', '--workspace',
                                dest='workspace',
                                help='directory with edges.shp and node.shp '
                                     '(with elevation information)',
                                metavar='dir',
                                type=str)
            CLI._args = parser.parse_args()

            # When program starts print license header
            print(CLI._epilog.partition('\nREQUIREMENTS')[0])
        return CLI._args


class UsageException(Exception):

    def __init__(self, message=None):
        if message is None:
            message = ('\nFirst of all import a shapefile (-i option) to a '
                       'workspace directory (-w option)\n\n'
                       'Then run the program specifing the workspace to use '
                       '(with -w option)\n\n'
                       '(To print the help use -h option)')
        super(UsageException, self).__init__(message)
