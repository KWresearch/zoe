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

import zoe_api.config as config
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from tornado.wsgi import WSGIContainer

import zoe_api.rest_api
import zoe_api.zk_manager

log = logging.getLogger("api_main")


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

    logging.getLogger('kazoo').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger("tornado").setLevel(logging.DEBUG)

    log.info("Connecting to ZooKeeper")
    state_manager = zoe_api.zk_manager.ZKManager()
    config.singletons['zk_manager'] = state_manager

    log.info("Initializing API")
    app = zoe_api.rest_api.init(state_manager)

    log.info("Starting HTTP REST server...")
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

    http_server = HTTPServer(WSGIContainer(app))
    http_server.listen(args.listen_port, args.listen_address)  # Initialized like this it is single-threaded/single-process
    ioloop = IOLoop.instance()
    try:
        ioloop.start()
    except KeyboardInterrupt:
        state_manager.stop()
        print("CTRL-C detected, terminating")
