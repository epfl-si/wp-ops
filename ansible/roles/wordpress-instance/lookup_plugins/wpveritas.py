# (c) 2020, EPFL IDEV-FSD <idev-fsd@groupes.epfl.ch>

"""Look up desired state in the wp-veritas database.

Usage:

  lookup("wpveritas", "unitId")
  lookup("wpveritas", "stylesheet")
  lookup("wpveritas")    # Gives out the entire data structure

Configuration is done through Ansible variables:

`wpveritas_api_url`
: The URL to fetch the API endpoint from (without the `/v1/sites` suffix)
`wp_base_url`
: The URL of the WordPress site to look up
"""

# Important: this script requires Python 2.7 compatibility, as the
# ansible-runner Docker image that we currently use doesn't have
# Python 3.

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.errors import AnsibleError
from ansible.plugins.lookup import LookupBase
try:
    from urllib2 import urlopen
except ModuleNotFoundError:
    # Python 3.x
    from urllib.request import urlopen

import ssl
import json

class LookupModule(LookupBase):
    def run(self, terms, variables, **kwargs):
        if len(terms) > 1:
            raise AnsibleError('Usage: lookup("wpveritas", KEY)')

        wpveritas_api_url = self.get_var(variables, 'wpveritas_api_url')
        wp_site_base_url  = self.get_var(variables, 'wp_base_url')

        wpveritas_state = WpVeritas(wpveritas_api_url).get_site(url=wp_site_base_url)
        if not wpveritas_state and wp_site_base_url.endswith("/"):
            wpveritas_state = WpVeritas(wpveritas_api_url).get_site(url=wp_site_base_url[:-1])
        if not wpveritas_state:
            raise AnsibleError("Site {} not found in wp-veritas".format(wp_site_base_url))

        if terms:
            return [wpveritas_state[terms[0]]]
        else:
            return [wpveritas_state]

    def get_var(self, variables, var_name):
        self._templar.available_variables = variables   # Calls an @property.setter
        variables = self._templar.available_variables   # Calls a getter
        if var_name not in variables:
            raise AnsibleError('In order to use lookup("wpveritas", ...), please define variable %s' % var_name)
        return self._templar.template(variables[var_name], fail_on_undefined=True)


class WpVeritas(object):
    def __init__(self, wpveritas_api_url):
        self._wpveritas_api_url = wpveritas_api_url

    def get_site(self, url):
        whole_state = self._get_state(self._wpveritas_api_url)
        the_site = [s for s in whole_state if s['url'] == url]
        if len(the_site) == 1:
            return the_site[0]
        else:
            return {}

    _state_cache = {}

    @classmethod
    def _get_state(cls, wpveritas_api_url):
        if wpveritas_api_url not in cls._state_cache:
            cls._state_cache[wpveritas_api_url] = cls._do_fetch(wpveritas_api_url)
        return cls._state_cache[wpveritas_api_url]

    @classmethod
    def _do_fetch(cls, wpveritas_api_url):

        if "nip.io" in wpveritas_api_url:
            try:
                context = ssl.SSLContext(verify=False)
            except TypeError:
                # Python 2.7, see https://stackoverflow.com/a/28048260/435004
                context = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
        else:
            context = None

        handle = urlopen(wpveritas_api_url + '/v1/sites', context=context)
        return json.loads(handle.read().decode('utf-8'))
