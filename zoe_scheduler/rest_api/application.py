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

import time

from werkzeug.exceptions import BadRequest
from flask_restful import Resource, request

from zoe_lib.exceptions import ZoeException, ZoeRestAPIException
from zoe_lib.metrics.influxdb import point, time_diff_ms
from zoe_scheduler.state.manager import StateManager
from zoe_scheduler.platform_manager import PlatformManager
from zoe_scheduler.rest_api.utils import catch_exceptions
from zoe_scheduler.rest_api.auth.authentication import authenticate
from zoe_scheduler.rest_api.auth.authorization import is_authorized
from zoe_scheduler.state.application import Application


class ApplicationAPI(Resource):
    """
    :type state: StateManager
    :type platform: PlatformManager
    """
    def __init__(self, **kwargs):
        self.state = kwargs['state']
        self.platform = kwargs['platform']

    @catch_exceptions
    def get(self, application_id: int):
        start = time.time()
        calling_user = authenticate(request, self.state)

        app = self.state.get_one('application', id=application_id)
        if app is None:
            raise ZoeRestAPIException('No such application', 404)

        is_authorized(calling_user, app, 'get')
        ret = app.to_dict(checkpoint=False)

        end = time.time()
        point('service_time', time_diff_ms(start, end), action='get', object='application', user=calling_user.name)
        return ret

    @catch_exceptions
    def delete(self, application_id: int):
        start = time.time()
        calling_user = authenticate(request, self.state)

        app = self.state.get_one('application', id=application_id)
        if app is None:
            return
        assert isinstance(app, Application)

        is_authorized(calling_user, app, 'delete')

        if self.state.app_has_active_executions(app.id):
            raise ZoeRestAPIException('Application has active executions, cannot delete')

        for e in app.executions:
            self.state.delete('execution', e.id)

        self.state.delete('application', app.id)

        self.state.state_updated()

        end = time.time()
        point('service_time', time_diff_ms(start, end), action='delete', object='application', user=calling_user.name)
        return '', 204


class ApplicationCollectionAPI(Resource):
    """
    :type state: StateManager
    :type platform: PlatformManager
    """
    def __init__(self, **kwargs):
        self.state = kwargs['state']
        self.platform = kwargs['platform']

    @catch_exceptions
    def post(self):
        start = time.time()
        calling_user = authenticate(request, self.state)

        try:
            data = request.get_json()
        except BadRequest:
            raise ZoeRestAPIException('Error decoding JSON data')

        app = Application(self.state)
        data['user_id'] = calling_user.id
        try:
            app.from_dict(data, checkpoint=False)
        except ZoeException as e:
            raise ZoeRestAPIException(str(e))

        is_authorized(calling_user, app, 'create')

        app.id = self.state.gen_id()
        self.state.new('application', app)
        self.state.state_updated()

        end = time.time()
        point('service_time', time_diff_ms(start, end), action='post', object='application', user=calling_user.name)
        return {'application_id': app.id}, 201
