#!/usr/bin/env python

# All rights reserved. ECOLE POLYTECHNIQUE FEDERALE DE LAUSANNE, Switzerland, VPSI, 2019
#
# Build an Ansible inventory from wp-veritas
# this file is found in https://github.com/epfl-idevelop/wp-ops under
# subdirectory ansible/tower/inventory_scripts
#
# Example invocation:
#    wp-veritas-inventory.py

import os.path
import subprocess
import sys
import logging


import json

import requests
from six.moves.urllib.parse import urlparse, quote

from StringIO import StringIO


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
        if site_data['status'] != 'created' or \
           site_data['type'] == 'unmanaged' or \
           site_data['url'] == '' or \
           site_data['openshiftEnv'] == '' or \
           site_data['openshiftEnv'] == 'manager' or \
           site_data['openshiftEnv'] == 'subdomains':
            return False
        else:
            return True

    def __init__(self, site_data):
        self.id = site_data['_id']
        self.url = site_data['url']
        self.parsed_url = urlparse(site_data['url'])
        self.tagline = site_data['tagline']
        self.title = site_data['title']
        self.openshift_env = site_data['openshiftEnv']
        self.category = site_data['category']
        self.theme = site_data['theme']
        self.faculty = site_data['faculty']
        self.languages = site_data['languages']
        self.unit_id = site_data['unitId']

    @property
    def instance_name(self):
        path = self.parsed_url.path
        # dont override groups name with hosts name
        # labs are in www, it's a special case
        if self.openshift_env == 'labs':
            instance_name = path
        else:
            instance_name = self.openshift_env + path

        # always clear instance_name last separator
        instance_name = (instance_name[:1] if instance_name.endswith('/') else instance_name)
        if not instance_name.startswith('/'):
            instance_name = '/' + instance_name

        return instance_name

    @property
    def wp_veritas_url(self):
        return 'https://wp-veritas.epfl.ch/edit/' + self.id

    # path on disk is not a provided data, so we have to build it
    @property
    def path(self):
        return os.path.join('/srv', self.openshift_env, self.parsed_url.netloc,
                            'htdocs', self.parsed_url.path)


class OpenShiftDeploymentConfig:
    OC_API_URL = 'https://pub-os-exopge.epfl.ch/api/v1/'
    OC_PROJECT_NAME = 'wwp'
    OC_KEY_FILE = '/run/secrets/kubernetes.io/serviceaccount/token'

    _cache = {}

    @classmethod
    def by_name(cls, dc_name):
        if dc_name not in cls._cache:
            cls._cache[dc_name] = cls(dc_name)
        return cls._cache[dc_name]

    def __init__(self, dc_name):
        self.dc_name = dc_name
        self._oc_data = self._fetch_oc_for_info(dc_name)

    def _fetch_oc_for_info(self, dc_name):
        token = ""

        if os.path.exists(self.OC_KEY_FILE):
            with open(self.OC_KEY_FILE) as token_file:
                token = token_file.read()
        else:
            token = subprocess.check_output(["oc", "whoami", "-t"]).rstrip()

        if token == "":
            raise Exception("Can't read the OC token on %s" % self.OC_KEY_FILE)
        else:
            token = 'Bearer ' + token

        url = self.OC_API_URL + 'namespaces/' + self.OC_PROJECT_NAME + '/pods'

        # add selector
        url += '?labelSelector=' + quote("app in (httpd-%s)" % dc_name)

        logging.debug('Fetching OC pods list from ' + url)
        headers = {'Authorization': token}

        r = requests.get(url, headers=headers, verify=True)

        if not r.ok:
            r.raise_for_status()

        return r.json()

    @property
    def pod_name(self):
        oc_data = self._oc_data
        if oc_data['items']:
            for item in oc_data['items']:
                if 'name' in item['metadata'] and item['metadata']['name']:
                    return item['metadata']['name']
        logging.error('Pods httpd-%s does not exist into the OC project %s' % (self.dc_name, self.OC_PROJECT_NAME))
        return None


class Inventory:
    """Model the entire wp-veritas inventory."""

    def __init__(self):
        self.inventory = {
            '_meta': {'hostvars': {}}
        }

    def _fulfill_pod_structure(self):
        """Add static data about group vars, if we any instance in it"""
        for key in self.inventory.keys():
            if key == '_meta':
                # ignore _meta, this is not a pod, only an ansible key
                continue

            ansible_oc_pod = OpenShiftDeploymentConfig.by_name(key).pod_name
            if ansible_oc_pod is not None:
                logging.debug("ansible pod found %s for %s" % (ansible_oc_pod, key))

                self.inventory[key]['vars'] = {
                    "wp_hostname": "www.epfl.ch",
                    "ansible_connection": "oc",
                    "ansible_oc_pod": ansible_oc_pod,
                    "ansible_oc_namespace": key,
                    "ansible_oc_container": "httpd-" + key,
                }

    @classmethod
    def build_as_string(cls):
        self = cls()
        for site in WpVeritasSite.all():
            self.add(site)
        self._fulfill_pod_structure()

        io = StringIO()
        json.dump(self.inventory, io, indent=2)
        return io.getvalue()

    def add(self, site):
        # fulfill vars for the site
        meta_site = {
            "wp_veritas_url": site.wp_veritas_url,
            "url": site.url,
            "tagline": site.tagline,
            "title": site.title,
            "openshift_env": site.openshift_env,
            "category": site.category,
            "theme": site.theme,
            "faculty": site.faculty,
            "languages": site.languages,
            "unit_id": site.unit_id,
            "wp_path": site.path
        }
        instance_name = site.instance_name
        self.inventory.setdefault(site.openshift_env, {}).setdefault('hosts', []).append(instance_name)
        self.inventory['_meta']['hostvars'][instance_name] = meta_site


def main():
    return sys.stdout.write(Inventory.build_as_string())


if __name__ == '__main__':
    main()
