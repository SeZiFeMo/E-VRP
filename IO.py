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

import logging
import utility
import yaml


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
