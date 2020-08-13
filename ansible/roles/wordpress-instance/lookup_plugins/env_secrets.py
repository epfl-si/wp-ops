# (c) 2020, EPFL IDEV-FSD <idev-fsd@groupes.epfl.ch>

"""Look up a secret either from the `env_secrets` Ansible variable, or from the environment.

This is mainly intended for Ansible tasks that require wielding secrets, and
that must also work on AWX / Ansible Tower / the mgmt pod (where Keybase is not
available, for security reasons). For instance, the following piece of Jinja

    lookup("env_secrets", "mysql_super_credentials", "MYSQL_SUPER_PASSWORD")

is the same as `lookup("env", "MYSQL_SUPER_PASSWORD")` on AWX, and the same as
`env_secrets.mysql_super_credentials.MYSQL_SUPER_PASSWORD` on the operator's
workstation.

Usage:

- To produce an env_secrets section: simply add it to ../../../vars/env-secrets.yml

- To convey an env_secrets section into AWX or the mgmt pod: evaluate it (sans
lookup), make a Kubernetes secret out of it (you may find the `base64_values`
Jinja filter useful for this sub-task), and expose it to the pod as a set of
environment variables.

- To consume an env_secrets section in a portable manner: see above.

"""

from ansible.errors import AnsibleError
from ansible.plugins.lookup import LookupBase

import os

def cached(fn):
    cache_key = '__cached_' + fn.__name__
    def uncached(self_or_cls):
        if not hasattr(self_or_cls, cache_key):
            setattr(self_or_cls, cache_key, fn(self_or_cls))
        return getattr(self_or_cls, cache_key)
    return uncached


class LookupModule(LookupBase):
    @classmethod
    @cached
    def _has_secrets(cls):
        return os.path.exists("/keybase")

    def run(self, terms, variables, **kwargs):
        if len(terms) != 2:
            raise AnsibleError('Usage: lookup("env_secrets", SECTION, KEY)')
        [section, key] = terms

        if self._has_secrets():
            self._templar.available_variables = variables
            return [self._templar.template(variables["env_secrets"])[section][key]]
        else:
            return [os.getenv(key)]
