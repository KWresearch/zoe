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

from zoe_lib.sql_manager import Execution, Service
from zoe_master.exceptions import ZoeStartExecutionRetryException, ZoeStartExecutionFatalException, ZoeException
from zoe_master.config import get_conf, singletons
from zoe_lib.swarm_client import DockerContainerOptions, SwarmClient
import zoe_master.workspace.base

log = logging.getLogger(__name__)


def execution_to_containers(execution: Execution):
    ordered_service_list = sorted(execution.services, key=lambda x: x.description['startup_order'])

    env_subst_dict = {
        "execution_name": execution.name,
        'user_name': execution.user_id,
        'deployment_name': get_conf().deployment_name,
    }

    for service in ordered_service_list:
        env_subst_dict['dns_name#' + service.name] = service.dns_name

    for service in ordered_service_list:
        env_subst_dict['dns_name#self'] = service.dns_name
        service.set_starting()
        _spawn_service(execution, service, env_subst_dict)


def _spawn_service(execution: Execution, service: Service, env_subst_dict: dict):
    copts = DockerContainerOptions()
    copts.gelf_log_address = get_conf().gelf_address
    copts.name = service.dns_name
    copts.set_memory_limit(service.description['required_resources']['memory'])
    copts.network_name = get_conf().overlay_network_name
    copts.labels = {
        'zoe.execution.name': execution.name,
        'zoe.execution.id': str(execution.id),
        'zoe.service.name': service.name,
        'zoe.service.id': str(service.id),
        'zoe.owner': execution.user_id,
        'zoe.deployment_name': get_conf().deployment_name,
        'zoe.type': 'app_service'
    }
    if service.description['monitor']:
        copts.labels['zoe.monitor'] = 'true'
    else:
        copts.labels['zoe.monitor'] = 'false'
    copts.restart = not service.description['monitor']  # Monitor containers should not restart

    # Generate a dictionary containing the current cluster status (before the new container is spawned)
    # This information is used to substitute template strings in the environment variables
    for env_name, env_value in service.description['environment']:
        try:
            env_value = env_value.format(**env_subst_dict)
        except KeyError:
            raise ZoeStartExecutionFatalException("unknown variable in expression {}".format(env_value))
        copts.add_env_variable(env_name, env_value)

    for p in service.description['ports']:
        if p['expose']:
            copts.ports.append(p['port_number'])  # FIXME UDP ports?

    if 'volumes' in service.description:
        for path, mount_point, readonly in service.description['volumes']:
            copts.add_volume_bind(path, mount_point, readonly)

    for wks in singletons['workspace_managers']:
        assert isinstance(wks, zoe_master.workspace.base.ZoeWorkspaceBase)
        if wks.can_be_attached():
            copts.add_volume_bind(wks.get_path(execution.user_id), wks.get_mountpoint(), False)

    # The same dictionary is used for templates in the command
    if 'command' in service.description:
        copts.set_command(service.description['command'].format(**env_subst_dict))

    try:
        swarm = SwarmClient(get_conf())
    except Exception as e:
        raise ZoeStartExecutionFatalException(str(e))

    try:
        cont_info = swarm.spawn_container(service.description['docker_image'], copts)
    except ZoeException as e:
        raise ZoeStartExecutionRetryException(str(e))

    service.set_active(cont_info["docker_id"])

    if 'networks' in service.description:
        for net in service.description['networks']:
            try:
                swarm.connect_to_network(service.docker_id, net)
            except ZoeException as e:
                raise ZoeStartExecutionFatalException(str(e))

    return


def terminate_execution(execution: Execution) -> None:
    execution.set_cleaning_up()
    swarm = SwarmClient(get_conf())
    for s in execution.services:
        assert isinstance(s, Service)
        if s.docker_id is not None:
            s.set_terminating()
            swarm.terminate_container(s.docker_id, delete=True)
            s.set_inactive()
            log.debug('Service {} terminated'.format(s.name))
    execution.set_terminated()
