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

import json
import logging

import kazoo.client
import kazoo.exceptions

import zoe_api.config
import zoe_api.version
from zoe_api.exceptions import ZoeException

log = logging.getLogger(__name__)


class ZKManager:
    def __init__(self):
        self.connection_status = 'lost'
        self.base_path = '/zoe/' + zoe_api.config.get_conf().deployment_name
        self.zk_address = zoe_api.config.get_conf().zk
        self.cli = kazoo.client.KazooClient(hosts=self.zk_address)
        self.cli.add_listener(self.zk_connection_state_cb)
        self.cli.start()
        self.cli.ensure_path(self.base_path + '/state_version')
        state_version, zk_meta = self._get_str(self.base_path + '/state_version')
        if len(state_version) > 0 and state_version != zoe_api.version.ZOE_STATE_VERSION:
            raise ZoeException('State version mismatch: can use {}, stored {}'.format(zoe_api.version.ZOE_STATE_VERSION, state_version))
        else:
            self._set_str(self.base_path + '/state_version', zoe_api.version.ZOE_STATE_VERSION)

    def _set_str(self, path, value, version=-1):
        self.cli.set(path, value.encode('utf-8'), version)

    def _get_str(self, path):
        data, stat = self.cli.get(path)
        return data.decode('utf-8'), stat

    def stop(self):
        self.cli.stop()

    def zk_connection_state_cb(self, state):
        if state == kazoo.client.KazooState.LOST:
            log.warn('Zookeeper connection lost')
            self.connection_status = 'lost'
        elif state == kazoo.client.KazooState.SUSPENDED:
            log.warn('Zookeeper connection suspended')
            self.connection_status = 'suspended'
        else:
            log.warn('Zookeeper connection OK')
            self.connection_status = 'connected'

    def get_service(self, exec_id, service_id):
        service_path = '{}/executions/{}/services/{}'.format(self.base_path, exec_id, service_id)
        try:
            description, description_meta = self._get_str(service_path + '/description')
            swarm_status, swarm_status_meta = self._get_str(service_path + '/swarm_status')
            expected_status, expected_status_meta = self._get_str(service_path + '/expected_status')
        except kazoo.exceptions.NoNodeError:
            return None

        description = json.loads(description)
        assert isinstance(description, dict)
        return {
            'name': service_id,
            'description': description,
            'swarm_status': swarm_status,
            'expected_status': expected_status
        }

    def list_services(self, exec_id):
        service_path = '{}/executions/{}/services'.format(self.base_path, exec_id)
        slist = self.cli.get_children(service_path)
        return slist

    def get_execution(self, exec_id):
        exec_path = '{}/executions/{}'.format(self.base_path, exec_id)
        try:
            app_description, app_description_meta = self._get_str(exec_path + '/app_descr')
            status, status_meta = self._get_str(exec_path + '/status')
            name, name_meta = self._get_str(exec_path + '/name')
        except kazoo.exceptions.NoNodeError:
            return None

        app_description = json.loads(app_description)
        assert isinstance(app_description, dict)
        return {
            'name': name,
            'app_description': app_description,
            'status': status,
        }

    def execution_is_active(self, exec_id):
        exec_path = '{}/executions/{}'.format(self.base_path, exec_id)
        status = self._get_str(exec_path + '/status')
        if status in ['submitted', 'parsing', 'starting', 'running']:
            return True
        else:
            return False

    def terminate_execution(self, exec_id):
        exec_path = '{}/executions/{}'.format(self.base_path, exec_id)

        status, status_meta = self._get_str(exec_path + '/status')
        while True:
            if status in ['submitted', 'parsing']:
                new_status = 'state_clean_up'
            elif status in ['starting', 'running']:
                new_status = 'terminating'
            else:
                break
            try:
                self.cli.set(exec_path + '/status', new_status, status_meta.version)
            except kazoo.exceptions.BadVersionError:
                status, status_meta = self._get_str(exec_path + '/status')
            else:
                break

    def list_executions(self):
        exec_path = '{}/executions'.format(self.base_path)
        exec_list = self.cli.get_children(exec_path)
        return exec_list

    def new_execution(self, app_descr):
        exec_path = self.cli.create(self.base_path + '/executions', sequence=True)
        exec_id = exec_path.split('/')[:-1]
        app_descr = json.dumps(app_descr)
        self.cli.create(exec_path + '/app_descr', value=app_descr.encode('utf-8'))
        self.cli.create(exec_path + '/status', value='submitted'.encode('utf-8'))
        return exec_id
