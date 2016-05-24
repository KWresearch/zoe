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

from zoe_api.rest_api.execution import ExecutionHandler
from zoe_api.rest_api.service import ServiceHandler
from zoe_api.rest_api.info import InfoHandler
from zoe_api.version import ZOE_API_VERSION

API_PATH = '/api/' + ZOE_API_VERSION

API_ROUTING = [
    (API_PATH + '/info', InfoHandler),
    (API_PATH + '/execution', ExecutionHandler),
    (API_PATH + '/service', ServiceHandler),
]
