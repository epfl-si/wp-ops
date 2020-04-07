#!/usr/bin/env python3

# All rights reserved. ECOLE POLYTECHNIQUE FEDERALE DE LAUSANNE, Switzerland, VPSI, 2019
#
# Build an Ansible inventory from wp-veritas
# this file is found in https://github.com/epfl-si/wp-ops under
# subdirectory ansible/tower/inventory_scripts
#
# Example invocation:
#    wp-veritas-inventory.py

import os.path
import subprocess
import sys
import logging

import re
import json
from urllib.parse import urlparse
import requests
from six.moves.urllib.parse import urlparse, quote

class WpVeritasSite:
    WP_VERITAS_SITES_API_URL = 'https://wp-veritas.epfl.ch/api/v1/sites/'
    VERIFY_SSL = True

    @classmethod
    def all(cls):
        logging.debug('Fetching sites from  ' + cls.WP_VERITAS_SITES_API_URL)
        r = requests.get(cls.WP_VERITAS_SITES_API_URL, verify=cls.VERIFY_SSL)

        if not r.ok:
            r.raise_for_status()
        for site in r.json():
            if cls._keep(site):
                yield cls(site)

    @classmethod
    def _keep(cls, site_data):
        if site_data['wpInfra'] is False or \
           site_data['url'] == '' or \
           site_data['openshiftEnv'] == '' or \
           site_data['openshiftEnv'].startswith('unm-') or \
           site_data['openshiftEnv'] == 'manager' or \
           site_data['openshiftEnv'] == 'subdomains':
            return False
        else:
            return True

    def __init__(self, site_data):
        try:
            self.url = site_data['url']
            self.parsed_url = urlparse(site_data['url'])
            self.openshift_env = site_data['openshiftEnv']
            self.category = site_data['category']
            self.theme = site_data['theme']
            self.languages = site_data['languages']
            self.unit_id = site_data['unitId']
            self.unit_name = site_data['unitName']
        except KeyError as e:
            logging.debug("Error: Missing field in provided data: %s" % site_data)
            raise e


    @property
    def instance_name(self):
        """
        Generates an unique nickname for a WP instance.

        :param site: Dict with WP information
        """
        path = self.parsed_url.path

        hostname = self.parsed_url.netloc
        hostname = re.sub(r'\.epfl\.ch$', '', hostname)
        hostname = re.sub(r'\W', '_', hostname)

        if path == "":
            return hostname
        else:
            path = re.sub(r'\/$', '', path)
            path = re.sub(r'^\/', '', path)
            path = re.sub(r'\/', '__', path)
            path = re.sub(r'\W', '_', path)
            return "{}__{}".format(hostname, path)

    @property
    def hostvars(self):
        hostvars = {
            "wp_env": self.openshift_env,
            "wp_hostname": self.parsed_url.netloc,
            "wp_path": re.sub(r'^/', '', self.parsed_url.path),
            "openshift_namespace": self._openshift_namespace
        }

        # Adding more information to site
        hostvars.update(self._connection_props())

        return hostvars

    def _connection_props(self):
        if Environment.is_awx():
            return { 'ansible_connection': 'local' }
        else:
            return {
                'ansible_host': self._mgmt_ssh_host,
                'ansible_port': '32222',
                'ansible_python_interpreter': '/usr/bin/python3',
                'ansible_user': 'www-data'
            }

    @property
    def _openshift_namespace(self):
        return 'wwp-prod'

    @property
    def _mgmt_ssh_host(self):
        return 'ssh-wwp.epfl.ch'


class WpVeritasTestSite(WpVeritasSite):
    WP_VERITAS_SITES_API_URL = 'https://wp-veritas.128.178.222.83.nip.io/api/v1/sites'
    VERIFY_SSL = False

    @property
    def instance_name(self):
        return 'test_' + super().instance_name


class Inventory:
    """Model the entire wp-veritas inventory."""

    def __init__(self, sites):

        self.inventory = {
            '_meta': {'hostvars': {}}
        }
        self.groups = set()
        for site in sites:
            self._add(site)


    def to_json(self):
        return json.dumps(self.inventory, sort_keys=True, indent=4)

    def _add(self, site):
        self.inventory['_meta']['hostvars'][site.instance_name] = site.hostvars
        self._add_site_to_group(site, site.openshift_env)

    def _add_site_to_group(self, site, openshift_env):
        group = 'prod-{}'.format(openshift_env)
        self._add_group(group)
        self.inventory[group]['hosts'].append(site.instance_name)

    def _add_group(self, group):
        if group in self.groups:
            return
        self.groups.add(group)
        self.inventory.setdefault('all-wordpresses', {}).setdefault('children', []).append(group)
        self.inventory.setdefault(group, {}).setdefault('hosts', [])


def cached(fn):
    cache_key = '__cached_' + fn.__name__
    def uncached(self_or_cls):
        if not hasattr(self_or_cls, cache_key):
            setattr(self_or_cls, cache_key, fn(self_or_cls))
        return getattr(self_or_cls, cache_key)
    return uncached


def to_string(string_or_bytes):
    if hasattr(string_or_bytes, 'decode'):
        return string_or_bytes.decode()
    else:
        return string_or_bytes


class Environment:
    @classmethod
    def is_awx(cls):
        # We don't really have or need a situation in which we run the
        # inventory on the cluster, except AWX.
        return cls.__is_on_openshift()

    @classmethod
    def __is_on_openshift(cls):
        return "system:serviceaccount:" in cls._oc_whoami()

    @classmethod
    @cached
    def _oc_whoami(cls):
        return subprocess.run(["oc", "whoami"], stdout=subprocess.PIPE).stdout.decode('utf-8')

    @classmethod
    def wpveritas_inventories(cls):
        if cls.is_awx():
            whoami = cls._oc_whoami()
            if 'wwp-test' in whoami:
                return ['test']
            elif 'wwp' in whoami:
                return ['prod']
            else:
                raise  ValueError('Unknown service account %s' % whoami)
        else:
            return os.environ.get('WPVERITAS_INVENTORIES', 'test').split(',')


if __name__ == '__main__':
    sites = []

    inventories = Environment.wpveritas_inventories()

    if 'test' in inventories:
        sites.extend(WpVeritasTestSite.all())

    if 'prod' in inventories:
        sites.extend(WpVeritasSite.all())

    sys.stdout.write(Inventory(sites).to_json())
