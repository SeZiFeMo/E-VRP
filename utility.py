#!/usr/bin/env python3
# coding: utf-8

""" E-VPR is a software developed for the Operational Research exam at
    University of Modena and Reggio Emilia; it is about the routing of
    a fleet of electrical vehicles.

    Copyright (C) 2017  Serena Ziviani, Federico Motta

    This file is part of E-VRP.

    E-VRP is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    E-VRP is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with E-VRP.  If not, see <http://www.gnu.org/licenses/>.
"""
__author__ = "Federico Motta, Serena Ziviani"
__license__ = "GPL3"

import argparse
import IO
import sys


# ------------------------------ SCRIPT LOADED ------------------------------ #
if __name__ == '__main__':
    IO.Log.warning('Please do not run that script, load it!')
    exit(1)

def check_python_version():
    if sys.version_info < (3,):
        major, minor, *__ = sys.version_info
        IO.Log.warning('You are using the Python interpreter {}.{}.\n'
                       'Please use at least Python version 3!'.format(major,
                                                                      minor))
        exit(1)
    else:
        return True


class CLI(object):

    _args = None
    _description = "E-VPR "                                                   \
        "Copyright (C) 2017 Serena Ziviani, Federico Motta\n"                \
        "This program comes with ABSOLUTELY NO WARRANTY.\n"                   \
        "This is free software, and you are welcome to redistribute it\n"     \
        "under certain conditions; read LICENSE file for more details.\n"
    _epilog = 'REQUIREMENTS: Python 3 (>= 3.6)\n'                             \
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
#            parser.add_argument('-a', '--aa',
#                                default='Default_value',
#                                dest='Variable_name_which_get_the_value',
#                                help='Text_shown_in_help',
#                                metavar='Value_printed_in_help_next_to_aa',
#                                type=str)  # Data type
            parser.add_argument('-i', '--input-file',
                                default='input.shp',
                                dest='input_file',
                                help='Shapefile to build initial graph (default input.shp)',
                                metavar='file',
                                type=str)
            group.add_argument('-q', '--quiet',
                               action='count',
                               default=0,
                               help='Set logging to WARNING, ERROR or '
                                    'CRITICAL (-q|-qq|-qqq)')
            group.add_argument('-v', '--verbose',
                               action='store_true',
                               help='Set logging to DEBUG '
                                    '(default level is INFO)')
            CLI._args = parser.parse_args()

            # When program starts print license header
            print(CLI._description)
        return CLI._args
