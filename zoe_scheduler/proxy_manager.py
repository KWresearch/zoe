from os import system
from urllib.parse import urlparse
import re
from datetime import datetime
import logging
log = logging.getLogger(__name__)

from jinja2 import Template

from common.configuration import conf
from common.state import AlchemySession, Proxy

LOOP_INTERVAL = 1  # seconds
ACCESS_TIME_REFRESH_INTERVAL = 60  # seconds

ENTRY_TEMPLATE = """
# Zoe proxy entry for service {{ service_name }}
<Location /proxy/{{ proxy_id }}>
    ProxyHtmlEnable On
    ProxyHTMLExtended On
    ProxyPass {{ proxy_url }} retry=1
    ProxyPassReverse {{ proxy_url }}
    {% if service_name != "Spark Notebook interface" %}
    ProxyHTMLURLMap ^/(.*)$ /proxy/{{ proxy_id }}/$1 RL
    ProxyHTMLURLMap ^logPage(.*)$ /proxy/{{ proxy_id }}/logPage$1 RL
    ProxyHTMLURLMap ^app(.*)$ /proxy/{{ proxy_id }}/app$1 RL
    {% for node in nodes %}
    ProxyHTMLURLMap ^http://{{ node[0] }}(.*)$ /proxy/{{node[1]}}$1 RL
    {% endfor %}
    {% endif %}
</Location>
{% if service_name == "Spark Notebook interface" %}
<Location /proxy/{{ proxy_id }}/ws/>
    ProxyPass ws://{{ netloc }}/proxy/{{ proxy_id }}/ws/
</Location>
{% endif %}
"""


class ProxyManager:
    def __init__(self):
        self.apache_conf_filepath = conf["apache-proxy-config-file"]
        self.apache_access_log = conf["apache-log-file"]

    def _get_proxy_entries(self):
        state = AlchemySession()
        return state.query(Proxy).all()

    def _generate_file(self, proxy_entries):
        output = ""
        jinja_template = Template(ENTRY_TEMPLATE)
        node_list = []
        for p in proxy_entries:
            netloc = urlparse(p.internal_url)[1]
            node_list.append((netloc, p.id))
        for p in proxy_entries:
            netloc = urlparse(p.internal_url)[1]
            jinja_dict = {
                "proxy_id": p.id,
                "proxy_url": p.internal_url,
                "service_name": p.service_name,
                "netloc": netloc,
                "nodes": node_list
            }
            apache_entry = jinja_template.render(jinja_dict)
            output += apache_entry + "\n"
        return output

    def _commit_and_reload(self, generated_file):
        open(self.apache_conf_filepath, "w").write(generated_file)
        system("sudo service apache2 reload")
        log.info("Apache reloaded")

    def update_proxy(self):
        entries = self._get_proxy_entries()
        output = self._generate_file(entries)
        self._commit_and_reload(output)

    def update_proxy_access_timestamps(self):
        regex = re.compile('[0-9.]+ - - \[(.*)\] "GET /proxy/([0-9a-z\-]+)/')
        logf = open(self.apache_access_log, 'r')
        last_accesses = {}
        for line in logf:
            match = re.match(regex, line)
            if match is not None:
                proxy_id = match.group(2)
                timestamp = datetime.strptime(match.group(1), "%d/%b/%Y:%H:%M:%S %z")
                last_accesses[proxy_id] = timestamp

        state = AlchemySession()
        for proxy in state.query(Proxy).all():
            if proxy.id in last_accesses:
                log.debug("Updating access timestamp for proxy ID {}".format(proxy.id))
                proxy = state.query(Proxy).filter_by(id=proxy.id).one()
                proxy.last_access = last_accesses[proxy.id]
                proxy.container.cluster.execution.termination_notice = False
                state.commit()

pm = ProxyManager()