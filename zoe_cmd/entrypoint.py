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

"""
This module contains the entrypoint for the commandline Zoe client
"""

import json
import logging
import os
import sys
from argparse import ArgumentParser, Namespace, FileType, RawDescriptionHelpFormatter
from pprint import pprint

from zoe_cmd import utils
from zoe_lib.applications import ZoeApplicationAPI
from zoe_lib.containers import ZoeContainerAPI
from zoe_lib.exceptions import ZoeAPIException
from zoe_lib.executions import ZoeExecutionsAPI
from zoe_lib.predefined_apps import hadoop, spark, lab_spark, test_sleep
from zoe_lib.query import ZoeQueryAPI
from zoe_lib.users import ZoeUserAPI

PREDEFINED_APPS = {}
for mod in [hadoop, spark, lab_spark, test_sleep]:
    for app_name, val in mod.__dict__.items():
        if callable(val) and "_app" in app_name:
            PREDEFINED_APPS[app_name[:-4]] = val


def stats_cmd(_):
    api = ZoeQueryAPI(utils.zoe_url(), utils.zoe_user(), utils.zoe_pass())
    stats = api.query('stats swarm')
    pprint(stats)


def user_new_cmd(args):
    api = ZoeUserAPI(utils.zoe_url(), utils.zoe_user(), utils.zoe_pass())
    name = args.name
    password = args.password
    role = args.role
    if role not in ['admin', 'user', 'guest']:
        print("Role must be one of admin, user, guest)")
        return
    user_id = api.create(name, password, role)
    print("New user ID: {}".format(user_id))


def user_get_cmd(args):
    api = ZoeQueryAPI(utils.zoe_url(), utils.zoe_user(), utils.zoe_pass())
    data = api.query('user', name=args.name)
    if len(data) == 0:
        print('No such user')
    else:
        user = data[0]
        print('User: {}'.format(user['name']))
        print('User ID: {}'.format(user['id']))
        print('Role: {}'.format(user['role']))
        print('Gateway URLs: {}'.format(user['gateway_urls']))


def user_delete_cmd(args):
    api_user = ZoeUserAPI(utils.zoe_url(), utils.zoe_user(), utils.zoe_pass())
    api_query = ZoeQueryAPI(utils.zoe_url(), utils.zoe_user(), utils.zoe_pass())
    data = api_query.query('user', name=args.name)
    if len(data) == 0:
        print('No such user')
    else:
        for user in data:
            print('Deleting user {}'.format(user['name']))
            api_user.delete(user['id'])


def user_list_cmd(_):
    api_query = ZoeQueryAPI(utils.zoe_url(), utils.zoe_user(), utils.zoe_pass())
    users = api_query.query('user')
    for user in users:
        print('<- User {} ->'.format(user['id']))
        print('User: {}'.format(user['name']))
        print('Role: {}'.format(user['role']))
        print('Gateway URLs: {}'.format(user['gateway_urls']))


def pre_app_list_cmd(_):
    for a in PREDEFINED_APPS.keys():
        print(a)


def pre_app_export_cmd(args):
    try:
        func = PREDEFINED_APPS[args.app_name]
    except KeyError:
        print('Application not found')
    else:
        app = func()
        json.dump(app, sys.stdout, sort_keys=True, indent=4)
        print()


def app_new_cmd(args):
    app_descr = json.load(args.jsonfile)
    api = ZoeApplicationAPI(utils.zoe_url(), utils.zoe_user(), utils.zoe_pass())
    try:
        app_id = api.create(app_descr)
    except ZoeAPIException as e:
        print("Invalid application description: %s" % e.message)
        return
    print("Application added with ID: {}".format(app_id))


def app_get_cmd(args):
    api_query = ZoeQueryAPI(utils.zoe_url(), utils.zoe_user(), utils.zoe_pass())
    data = api_query.query('application', name=args.name)
    if len(data) == 0:
        print("no such application")
    else:
        for app in data:
            pprint(app)


def app_rm_cmd(args):
    api_app = ZoeApplicationAPI(utils.zoe_url(), utils.zoe_user(), utils.zoe_pass())
    api_query = ZoeQueryAPI(utils.zoe_url(), utils.zoe_user(), utils.zoe_pass())
    data = api_query.query('application', name=args.name)
    if len(data) == 0:
        print('No such application')
    else:
        for app in data:
            print('Deleting app {}'.format(app['name']))
            api_app.delete(app['id'])


def app_list_cmd(_):
    api_query = ZoeQueryAPI(utils.zoe_url(), utils.zoe_user(), utils.zoe_pass())
    data = api_query.query('application')
    for app in data:
        print('{} (ID: {})'.format(app['name'], app['id']))


def exec_list_cmd(_):
    exec_api = ZoeExecutionsAPI(utils.zoe_url(), utils.zoe_user(), utils.zoe_pass())
    data = exec_api.list()
    for e in data:
        print('Execution {} (ID: {}): {}'.format(e['name'], e['id'], e['status']))


def exec_start_cmd(args):
    exec_api = ZoeExecutionsAPI(utils.zoe_url(), utils.zoe_user(), utils.zoe_pass())
    ret = exec_api.execution_start(args.name, args.app_name)
    print("Application scheduled successfully with ID {}, use the exec-get command to check its status".format(ret))


def exec_get_cmd(args):
    app_api = ZoeApplicationAPI(utils.zoe_url(), utils.zoe_user(), utils.zoe_pass())
    exec_api = ZoeExecutionsAPI(utils.zoe_url(), utils.zoe_user(), utils.zoe_pass())
    cont_api = ZoeContainerAPI(utils.zoe_url(), utils.zoe_user(), utils.zoe_pass())
    execution = exec_api.execution_get(args.id)
    if execution is None:
        print('Execution not found')
    else:
        print('Execution {} (ID: {})'.format(execution['name'], execution['id']))
        print('Status: {}'.format(execution['status']))
        print('Time started: {}'.format(execution['time_started']))
        print('Time scheduled: {}'.format(execution['time_scheduled']))
        print('Time finished: {}'.format(execution['time_finished']))
        app = app_api.get(execution['application_id'])
        print('Application name: {}'.format(app['name']))
        for c_id in execution['containers']:
            c = cont_api.get(c_id)
            ip = list(c['ip_address'].values())[0]  # FIXME how to decide which network is the right one?
            print('Container {} (ID: {})'.format(c['name'], c['id']))
            for p in c['ports']:
                print(' - {}: {}://{}:{}{}'.format(p['name'], p['protocol'], ip, p['port_number'], p['path']))


def exec_kill_cmd(args):
    exec_api = ZoeExecutionsAPI(utils.zoe_url(), utils.zoe_user(), utils.zoe_pass())
    exec_api.terminate(args.id)


def log_get_cmd(args):
    cont_api = ZoeContainerAPI(utils.zoe_url(), utils.zoe_user(), utils.zoe_pass())
    log = cont_api.log(args.container_id)
    if log is None:
        print("Error: No log found for container ID {}".format(args.container_id))
        return
    try:
        print(log)
    except BrokenPipeError:
        pass


def container_stats_cmd(args):
    cont_api = ZoeContainerAPI(utils.zoe_url(), utils.zoe_user(), utils.zoe_pass())
    stats = cont_api.stats(args.container_id)
    print(stats)


ENV_HELP_TEXT = '''To use this tool you need also to define three environment variables:
ZOE_URL: point to the URL of the Zoe Scheduler (ex.: http://localhost:5000/
ZOE_USER: the username used for authentication
ZOE_PASS: the password used for authentication'''


def process_arguments() -> Namespace:
    parser = ArgumentParser(description="Zoe command-line client", epilog=ENV_HELP_TEXT, formatter_class=RawDescriptionHelpFormatter)
    parser.add_argument('--debug', action='store_true', help='Enable debug output')

    subparser = parser.add_subparsers()

    argparser_stats = subparser.add_parser('stats', help="Show the platform statistics")
    argparser_stats.set_defaults(func=stats_cmd)

    argparser_user_new = subparser.add_parser('user-new', help="Create a new user")
    argparser_user_new.add_argument('--name', help="User name")
    argparser_user_new.add_argument('--password', help="Password")
    argparser_user_new.add_argument('--role', help="Role (one of admin, user, guest)")
    argparser_user_new.set_defaults(func=user_new_cmd)

    argparser_user_get = subparser.add_parser('user-get', help="Retrieve information about a user")
    argparser_user_get.add_argument('name', help="User name")
    argparser_user_get.set_defaults(func=user_get_cmd)

    argparser_user_delete = subparser.add_parser('user-rm', help="Removes a user from the system")
    argparser_user_delete.add_argument('name', help="User name")
    argparser_user_delete.set_defaults(func=user_delete_cmd)

    argparser_user_list = subparser.add_parser('user-list', help='Lists all users defined in the system')
    argparser_user_list.set_defaults(func=user_list_cmd)

    argparser_pre_app_list = subparser.add_parser('pre-app-list', help='Lists the predefined application descriptions')
    argparser_pre_app_list.set_defaults(func=pre_app_list_cmd)

    argparser_pre_app_export = subparser.add_parser('pre-app-export', help='Export one of the predefined application descriptions in JSON (stdout)')
    argparser_pre_app_export.add_argument('app_name', help='Predefined application name (use pre-app-list to see what is available')
    argparser_pre_app_export.set_defaults(func=pre_app_export_cmd)

    argparser_app_new = subparser.add_parser('app-new', help="Upload a JSON application description")
    argparser_app_new.add_argument('jsonfile', type=FileType("r"), help='Application description')
    argparser_app_new.set_defaults(func=app_new_cmd)

    argparser_app_get = subparser.add_parser('app-get', help="Retrieve an already defined application description")
    argparser_app_get.add_argument('name', help='The name of the application')
    argparser_app_get.set_defaults(func=app_get_cmd)

    argparser_app_rm = subparser.add_parser('app-rm', help="Delete an application")
    argparser_app_rm.add_argument('name', help="Application name (will fail if there are running executions)")
    argparser_app_rm.set_defaults(func=app_rm_cmd)

    argparser_app_list = subparser.add_parser('app-ls', help="List all applications defined by the calling user")
    argparser_app_list.set_defaults(func=app_list_cmd)

    argparser_exec_start = subparser.add_parser('start', help="Start a previously registered application")
    argparser_exec_start.add_argument('app_name', help="Name of the application to start")
    argparser_exec_start.add_argument('name', help="Name of the execution")
    argparser_exec_start.set_defaults(func=exec_start_cmd)

    argparser_execution_get = subparser.add_parser('exec-get', help="Get execution status")
    argparser_execution_get.add_argument('id', type=int, help="Execution id")
    argparser_execution_get.set_defaults(func=exec_get_cmd)

    argparser_app_list = subparser.add_parser('exec-ls', help="List all executions for the calling user")
    argparser_app_list.set_defaults(func=exec_list_cmd)

    argparser_execution_kill = subparser.add_parser('terminate', help="Terminates an execution")
    argparser_execution_kill.add_argument('id', type=int, help="Execution id")
    argparser_execution_kill.set_defaults(func=exec_kill_cmd)

    argparser_log_get = subparser.add_parser('log-get', help="Retrieves the logs of a running container")
    argparser_log_get.add_argument('container_id', type=int, help="Container id")
    argparser_log_get.set_defaults(func=log_get_cmd)

    argparser_container_stats = subparser.add_parser('container-stats', help="Retrieve statistics on a running container")
    argparser_container_stats.add_argument('container_id', type=int, help="ID of the container")
    argparser_container_stats.set_defaults(func=container_stats_cmd)

    return parser, parser.parse_args()


def zoe():
    parser, args = process_arguments()
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
    logging.getLogger("requests").setLevel(logging.WARNING)

    if not hasattr(args, "func"):
        parser.print_help()
        return

    if 'ZOE_URL' not in os.environ or 'ZOE_USER' not in os.environ or 'ZOE_PASS' not in os.environ:
        parser.print_help()
        return

    try:
        args.func(args)
    except ZoeAPIException as e:
        print(e.message)
    sys.exit(0)