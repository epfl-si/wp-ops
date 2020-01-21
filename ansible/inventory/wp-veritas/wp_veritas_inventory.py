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
        try:
            self.id = site_data['_id']
            self.url = site_data['url']
            self.parsed_url = urlparse(site_data['url'])
            self.tagline = site_data['tagline']
            self.title = site_data['title']
            self.openshift_env = site_data['openshiftEnv']
            self.category = site_data['category']
            self.theme = site_data['theme']
            self.languages = site_data['languages']
            self.unit_id = site_data['unitId']
        except KeyError, e:
            logging.debug("Error: Missing field in provided data: %s" % site_data)
            raise e


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
            if r.status_code == 401:
                logging.debug("""You are Unauthorized on this OC instance,
                 check/refresh your local key (by doing a "oc login") or verify the permissions.""")
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

    def __init__(self, sites):
        self.inventory = {
            '_meta': {'hostvars': {}}
        }
        self.groups = set()
        for site in sites:
            self._add(site)

    def to_json(self):
        io = StringIO()
        json.dump(self.inventory, io, indent=2)
        return io.getvalue()

    def _add(self, site):
        # fulfill vars for the site
        meta_site = {
            "wp_veritas_url": site.wp_veritas_url,
            "url": site.url,
            "tagline": site.tagline,
            "title": site.title,
            "openshift_env": site.openshift_env,
            "category": site.category,
            "theme": site.theme,
            "languages": site.languages,
            "unit_id": site.unit_id,
            "wp_path": site.path
        }
        self.inventory['_meta']['hostvars'][site.instance_name] = meta_site
        self._add_site_to_group(site, site.openshift_env)

    def _add_site_to_group(self, site, group):
        self._add_group(group)
        self.inventory[group]['hosts'].append(site.instance_name)

    def _add_group(self, group):
        if group in self.groups:
            return
        self.groups.add(group)

        self.inventory.setdefault('all-wordpresses', {}).setdefault('children', []).append(group)
        self.inventory.setdefault(group, {}).setdefault('hosts', [])
        self._fill_dc_group_info(group)

    def _fill_dc_group_info(self, group):
        """Add static data about group vars, if we any instance in it"""
        ansible_oc_pod = OpenShiftDeploymentConfig.by_name(group).pod_name
        if ansible_oc_pod is None:
            # This group is unknown to wp-veritas
            return

        logging.debug("ansible pod found %s for %s" % (ansible_oc_pod, group))

        self.inventory[group]['vars'] = {
            "wp_hostname": "www.epfl.ch",
            "ansible_connection": "oc",
            "ansible_python_interpreter": "/usr/bin/python3",
            "ansible_oc_pod": ansible_oc_pod,
            "wp_env": group,
            "ansible_oc_namespace": "wwp",
            "ansible_oc_container": "httpd-" + group,
        }


if __name__ == '__main__':
    #logging.basicConfig(level=logging.DEBUG)  # may be needed
    sys.stdout.write(Inventory(WpVeritasSite.all()).to_json())
