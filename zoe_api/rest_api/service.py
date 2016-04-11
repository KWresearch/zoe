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

from flask_restful import Resource, request

from zoe_api.rest_api.exceptions import ZoeRestAPIException
from zoe_api.rest_api.auth.authentication import authenticate
from zoe_api.rest_api.auth.authorization import is_authorized
from zoe_api.rest_api.utils import catch_exceptions
from zoe_api.zk_manager import ZKManager

log = logging.getLogger(__name__)


class ServiceAPI(Resource):
    """
    :type state: ZKManager
    """
    def __init__(self, **kwargs):
        self.state = kwargs['state']

    @catch_exceptions
    def get(self, execution_id, service_name):
        authenticate(request)
        is_authorized()

        s = self.state.get_service(execution_id, service_name)
        if s is None:
            raise ZoeRestAPIException('No such service', 404)

        assert isinstance(s, dict)
        return s


class ServiceCollectionAPI(Resource):
    """
    :type state: ZKManager
    """
    def __init__(self, **kwargs):
        self.state = kwargs['state']

    @catch_exceptions
    def get(self, execution_id):
        authenticate(request)
        is_authorized()

        s = self.state.list_services(execution_id)
        if s is None:
            raise ZoeRestAPIException('No such service', 404)

        assert isinstance(s, list)
        return {'services': s}
