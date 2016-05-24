#!/usr/bin/python3

# Copyright (c) 2016, Daniele Venzano
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging

import psycopg2.extras
from tornado.httpserver import HTTPServer
from tornado import web
from tornado.ioloop import IOLoop
import momoko

import zoe_api.config as config
import zoe_api.db_init
import zoe_api.web

log = logging.getLogger("entrypoint")


def make_app(conf):
    app = web.Application(zoe_api.web.WEB_ROUTING,
                          debug=conf.debug)
    return app


def main():
    """
    The entrypoint for the zoe-master script.
    :return: int
    """
    config.load_configuration()
    args = config.get_conf()
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)

    else:
        logging.basicConfig(level=logging.INFO)

    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger("tornado").setLevel(logging.DEBUG)

    log.info('Init DB')
    zoe_api.db_init.init(args)

    log.info("Starting HTTP server...")
    ioloop = IOLoop.instance()
    app = make_app(args)

    dsn = 'dbname=' + args.dbname + \
          ' user=' + args.dbuser + \
          ' password=' + args.dbpass + \
          ' host=' + args.dbhost + \
          ' port=' + str(args.dbport) + \
          ' options=-c\ search_path=' + args.deployment_name + ",public"
    app.db = momoko.Pool(dsn=dsn, cursor_factory=psycopg2.extras.DictCursor, ioloop=ioloop)

    future = app.db.connect()
    ioloop.add_future(future, lambda f: ioloop.stop())
    ioloop.start()
    future.result()  # raises exception on connection error

    http_server = HTTPServer(app)
    http_server.listen(args.listen_port, args.listen_address)
    try:
        ioloop.start()
    except KeyboardInterrupt:
        print("CTRL-C detected, terminating")
