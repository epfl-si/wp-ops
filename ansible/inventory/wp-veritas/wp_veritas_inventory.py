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

props_to_merge = {
    'ansible_host': 'ssh-wwp.epfl.ch',
    'ansible_port': '32222',
    'ansible_python_interpreter': '/usr/bin/python3',
    'ansible_user': 'www-data',
    'wp_ensure_symlink_version': '5.2',
    'openshift_namespace': 'wwp-prod'
}

class WpVeritasSite:
    WP_VERITAS_SITES_API_URL = 'https://wp-veritas.epfl.ch/api/v1/sites/'

    @classmethod
    def all(cls):
        logging.debug('Fetching sites from  ' + cls.WP_VERITAS_SITES_API_URL)
        r = requests.get(cls.WP_VERITAS_SITES_API_URL)

        if not r.ok:
            r.raise_for_status()
        for site in r.json():
            if cls._keep(site):
                yield cls(site)

    @classmethod
    def _keep(cls, site_data):
        if site_data['type'] == 'unmanaged' or \
           site_data['url'] == '' or \
           site_data['openshiftEnv'] == '' or \
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
            path = re.sub(r'\/', '_', path)
            return "{}__{}".format(hostname, path)


class Inventory:
    """Model the entire wp-veritas inventory."""

    def __init__(self, sites):

        self._nicknames_already_taken = []

        self.inventory = {
            '_meta': {'hostvars': {}}
        }
        self.groups = set()
        for site in sites:
            self._add(site)


    def to_json(self):
        return json.dumps(self.inventory, sort_keys=True, indent=4)

    def _add(self, site):

        wp_details = {
            'options' : {
                'epfl.site_category': site.category,
                'plugin:epfl_accred:unit_id': site.unit_id,
                'stylesheet': site.theme
            },
            'polylang': {
                'langs': site.languages
            }
        }

        # fulfill vars for the site
        meta_site = {
            "wp_env": site.openshift_env,
            "wp_hostname": site.parsed_url.netloc,
            "wp_path": re.sub(r'^/', '', site.parsed_url.path),
            "wp_details": wp_details
        }

        # Adding more information to site
        meta_site = {**meta_site, **props_to_merge}

        self.inventory['_meta']['hostvars'][site.instance_name] = meta_site
        self._add_site_to_group(site, site.openshift_env)

    def _add_site_to_group(self, site, openshift_env):
        group = 'prod-{}'.format(openshift_env)
        self._add_group(group)
        self.inventory[group]['hosts'].append(site.instance_name)

    def _add_group(self, group):
        if group in self.groups:
            return
        self.groups.add(group)

        #self.inventory.setdefault('prod-wordpresses', {}).setdefault('children', []).append(group)
        self.inventory.setdefault(group, {}).setdefault('hosts', [])


if __name__ == '__main__':
    #logging.basicConfig(level=logging.DEBUG)  # may be needed
    sys.stdout.write(Inventory(WpVeritasSite.all()).to_json())
