#!/usr/bin/env python
# -*- coding: utf-8 -*-

###############################################################################
#  Copyright 2013 Kitware Inc.
#
#  Licensed under the Apache License, Version 2.0 ( the "License" );
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
###############################################################################

import cherrypy
import click

from girder.utility import server


@click.command(name='serve', short_help='Run the Girder server.', help='Run the Girder server.')
@click.option('-t', '--testing', is_flag=True, help='Run in testing mode')
@click.option('-d', '--database', default=cherrypy.config['database']['uri'],
              show_default=True, help='The database URI to connect to')
@click.option('-H', '--host', default=cherrypy.config['server.socket_host'],
              show_default=True, help='The interface to bind to')
@click.option('-p', '--port', type=int, default=cherrypy.config['server.socket_port'],
              show_default=True, help='The port to bind to')
def main(testing, database, host, port):
    if database:
        cherrypy.config['database']['uri'] = database
    if host:
        cherrypy.config['server.socket_host'] = host
    if port:
        cherrypy.config['server.socket_port'] = port
    server.setup(testing)

    cherrypy.engine.start()
    cherrypy.engine.block()
