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
This module contains the Zoe Query API.
"""

import logging

from zoe_lib.api_base import ZoeAPIBase
from zoe_lib.exceptions import ZoeAPIException

log = logging.getLogger(__name__)


class ZoeQueryAPI(ZoeAPIBase):
    """
    The Query API class. This API can be used to query the state of Zoe.
    """
    def query(self, topic, **kwargs):
        """
        Queries Zoe state.

        :param topic:
        :param kwargs:
        :return:
        """
        q = {
            'what': topic,
            'filters': kwargs
        }

        data, status_code = self._rest_post('/query', q)
        if status_code != 200:
            raise ZoeAPIException(data['message'])
        else:
            return data
