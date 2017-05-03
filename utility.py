#!/usr/bin/env python3
# coding: utf-8

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
    _description = '\n' # TODO description
    _epilog = 'REQUIREMENTS: Python 3 (>= 3.6)\n'                             \
        '              Matplotlib   https://matplotlib.org\n'                 \
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
        return CLI._args
