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

from zoe_api.exceptions import ZoeException


def validate_service_endpoint(data):
    required_keys = ['name', 'protocol']
    for k in required_keys:
        try:
            data[k]
        except KeyError:
            raise ZoeException("Missing required key: %s" % k)

    try:
        int(data['port_number'])
    except ValueError:
        raise ZoeException("port_number field should be an integer")
    except KeyError:
        raise ZoeException("Missing required key: port_number")

    try:
        bool(data['is_main_endpoint'])
    except ValueError:
        raise ZoeException("is_main_endpoint field should be a boolean")
    except KeyError:
        raise ZoeException("Missing required key: is_main_endpoint")


def validate_service(data):
    required_keys = ['name', 'docker_image']
    for k in required_keys:
        try:
            data[k]
        except KeyError:
            raise ZoeException("Missing required key: %s" % k)

    try:
        bool(data['monitor'])
    except ValueError:
        raise ZoeException("monitor field should be a boolean")
    except KeyError:
        raise ZoeException("Missing required key: monitor")

    if 'ports' not in data:
        raise ZoeException("Missing required key: ports")
    if not hasattr(data['ports'], '__iter__'):
        raise ZoeException('ports should be an iterable')
    for pp in data['ports']:
        validate_service_endpoint(pp)

    if 'required_resources' not in data:
        raise ZoeException("Missing required key: required_resources")
    if not isinstance(data['required_resources'], dict):
        raise ZoeException("required_resources should be a dictionary")
    if 'memory' not in data['required_resources']:
        raise ZoeException("Missing required key: required_resources -> memory")

    try:
        int(data['required_resources']['memory'])
    except ValueError:
        raise ZoeException("required_resources -> memory field should be an int")

    if 'environment' in data:
        if not hasattr(data['environment'], '__iter__'):
            raise ZoeException('environment should be an iterable')
        for e in data['environment']:
            if len(e) != 2:
                raise ZoeException('environment variable should have a name and a value')
            if not isinstance(e[0], str):
                raise ZoeException('environment variable names must be strings: {}'.format(e[0]))
            if not isinstance(e[1], str):
                raise ZoeException('environment variable values must be strings: {}'.format(e[1]))

    if 'volumes' in data:
        if not hasattr(data['volumes'], '__iter__'):
            raise ZoeException('volumes should be an iterable')
        for v in data['volumes']:
            if len(v) != 3:
                raise ZoeException('volume description should have three components')
            if not isinstance(v[2], bool):
                raise ZoeException('readonly volume item (third) must be a boolean: {}'.format(v[2]))

    if 'networks' in data:
        if not hasattr(data['networks'], '__iter__'):
            raise ZoeException('networks should be an iterable')


def validate(data):
    if not hasattr(data, '__getitem__'):
        raise ZoeException("Application description should translate into a Python dictionary")

    if 'name' not in data:
        raise ZoeException("Missing required key: name")

    try:
        int(data['version'])
    except ValueError:
        raise ZoeException("version field should be an int")
    except KeyError:
        raise ZoeException("Missing required key: version")

    try:
        bool(data['will_end'])
    except ValueError:
        raise ZoeException("will_end field must be a boolean")

    try:
        bool(data['requires_binary'])
    except ValueError:
        raise ZoeException("requires_binary field must be a boolean")

    try:
        priority = int(data['priority'])
    except ValueError:
        raise ZoeException("priority field must be an int")
    if priority < 0 or priority > 1024:
        raise ZoeException("priority must be between 0 and 1024")

    for p in data['services']:
        validate_service(p)

    found_monitor = False
    for p in data['services']:
        if p['monitor']:
            found_monitor = True
            break
    if not found_monitor:
        raise ZoeException("at least one service should have monitor set to True")
