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

import zoe_api.config as config
import zoe_api.version

from zoe_api.rest_api.auth.authentication import authenticate
from zoe_api.rest_api.utils import catch_exceptions


class InfoAPI(Resource):
    """
    :type state: StateManager
    """
    def __init__(self, **kwargs):
        self.state = kwargs['state']

    @catch_exceptions
    def get(self):
        authenticate(request)

        ret = {
            'version': zoe_api.version.ZOE_VERSION,
            'api_version': zoe_api.version.ZOE_API_VERSION,
            'application_format_version': zoe_api.version.ZOE_APPLICATION_FORMAT_VERSION,
            'deployment_name': config.get_conf().deployment_name,
            'state_version': zoe_api.version.ZOE_STATE_VERSION
        }

        return ret
