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

from flask_restful import Resource, request
from werkzeug.exceptions import BadRequest

from zoe_api.rest_api.exceptions import ZoeRestAPIException
from zoe_api.rest_api.auth.authentication import authenticate
from zoe_api.rest_api.auth.authorization import is_authorized
from zoe_api.rest_api.utils import catch_exceptions
from zoe_api.application_validation import validate


class ExecutionAPI(Resource):
    """
    :type state: ZKManager
    """
    def __init__(self, **kwargs):
        self.state = kwargs['state']

    @catch_exceptions
    def get(self, execution_id: int):
        authenticate(request)
        is_authorized()

        e = self.state.get_execution(execution_id)
        if e is None:
            raise ZoeRestAPIException('No such execution', 404)

        assert isinstance(e, dict)
        return e

    @catch_exceptions
    def delete(self, execution_id: int):
        """
        This method is called when a user wants to stop an execution.
        :param execution_id: the execution to terminate
        """
        authenticate(request)
        is_authorized()

        if self.state.execution_is_active(execution_id):
            self.state.terminate_execution(execution_id)

        return '', 204


class ExecutionCollectionAPI(Resource):
    """
    :type state: ZKManager
    """
    def __init__(self, **kwargs):
        self.state = kwargs['state']

    @catch_exceptions
    def get(self):
        """
        Returns a list of all active executions.
        """
        authenticate(request)
        is_authorized()
        execs = self.state.list_executions()
        assert isinstance(execs, list)
        return {'executions': execs}

    @catch_exceptions
    def post(self):
        """
        Starts an execution, given an application description. Takes a JSON object.
        """
        authenticate(request)
        is_authorized()

        try:
            data = request.get_json()
        except BadRequest:
            raise ZoeRestAPIException('Error decoding JSON data')

        validate(data)

        exec_id = self.state.new_execution(data)

        return {'execution_id': exec_id}, 201
