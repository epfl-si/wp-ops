#!/usr/bin/env python3

# All rights reserved. ECOLE POLYTECHNIQUE FEDERALE DE LAUSANNE, Switzerland, VPSI, 2019
#
# Build an Ansible inventory from wp-veritas and/or the on-NFS state
#
# Example invocation:
#    env WWP_INVENTORY_SOURCES=wpveritas,nfs WWP_NAMESPACES=wwp-test,wwp wordpress-instances.py

import sys
import os
import glob

ansible_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ansible_suitcase_python_libs = glob.glob(os.path.join(
    ansible_dir, "ansible-deps-cache/python-libs/lib/*/site-packages"))

if len(ansible_suitcase_python_libs) > 0:
    sys.path.insert(0, ansible_suitcase_python_libs[0])

import subprocess
import logging
import re
from functools import reduce

import re
import json
import requests
import itertools
from six.moves.urllib.parse import urlparse, quote

import warnings
warnings.filterwarnings('ignore', message='Unverified HTTPS request')

class _Site:
    @property
    def hostvars(self):
        hostvars = {
            "wp_env": self.wwp_env,
            "wp_hostname": self.wp_hostname,
            "wp_path": self.wp_path,
            "openshift_namespace": self.k8s_namespace,
            "ansible_python_interpreter": '/usr/bin/python3'
        }
        if Environment.is_awx():
            hostvars.update({
                'ansible_connection': 'local'
                # No need for become; see runAsUser in the container spec
            })
        else:
            # TODO: at some point we will be forced to use oc instead of ssh.
            hostvars.update({
                'ansible_connection': 'ssh',
                'ansible_ssh_host': self._get_wwp_ssh_host(),
                'ansible_ssh_port': 32222,
                'ansible_ssh_user': 'www-data'
            })
        return hostvars

    def __init__(self, wwp_env, wp_hostname, wp_path):
        self.wwp_env = wwp_env
        self.wp_hostname = wp_hostname
        self.wp_path = wp_path

    def _keep(self):
        if self.wwp_env == '' or \
           self.wwp_env.startswith('unm-') or \
           self.wwp_env == 'manager':
            return False
        else:
            return True

    @property
    def group_hierarchy(self):
        def to_group_name_fragment(some_text):
            return re.sub('-', '_', some_text)

        return [
            '%s_%s' % (self.group_prefix, suffix)
            for suffix in (
                to_group_name_fragment(self.wwp_env),
                'wordpresses'
                )
            ]

    @property
    def instance_name(self):
        """
        Generates an unique nickname for a WP instance.

        :param site: Dict with WP information
        """
        path = self.wp_path

        hostname = self.wp_hostname
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

    def _get_wwp_ssh_host(self):
        ssh_hosts = {'wwp': 'ssh-wwp.epfl.ch',
                      'wwp-test': 'test-ssh-wwp.epfl.ch'}
        return ssh_hosts[self.k8s_namespace]


class ProdSiteTrait:
    k8s_namespace = 'wwp'
    group_prefix = 'prod'


class TestSiteTrait:
    k8s_namespace = 'wwp-test'
    group_prefix = 'test'

    @property
    def instance_name(self):
        return 'test_' + _Site.instance_name.fget(self)


class WpVeritasSite(ProdSiteTrait, _Site):
    WP_VERITAS_SITES_API_URL = 'https://wp-veritas.epfl.ch/api/v1/inventory/entries'
    VERIFY_SSL = True

    @classmethod
    def all(cls):
        logging.debug('Fetching sites from  ' + cls.WP_VERITAS_SITES_API_URL)
        r = requests.get(cls.WP_VERITAS_SITES_API_URL, verify=cls.VERIFY_SSL)

        if not r.ok:
            r.raise_for_status()
        for site_data in r.json():
            site = cls(site_data)
            if site._keep(site_data):
                yield site

    def _keep(self, site_data):
        if not super(WpVeritasSite, self)._keep():
            return False
        if site_data['wpInfra'] is False or \
           site_data['url'] == '':
            return False
        else:
            return True

    def __init__(self, site_data):
        try:
            self.url = site_data['url']
            self.parsed_url = urlparse(site_data['url'])
            super(WpVeritasSite, self).__init__(wwp_env=site_data['openshiftEnv'],
                                                wp_hostname=self.parsed_url.netloc,
                                                wp_path=re.sub(r'^/', '', self.parsed_url.path))
            self.categories = site_data['categories']
            self.theme = site_data['theme']
            self.languages = site_data['languages']
            self.unit_id = site_data['unitId']
            self.unit_name = site_data['unitName']
        except KeyError as e:
            logging.debug("Error: Missing field in provided data: %s" % site_data)
            raise e

    @property
    def hostvars(self):
        hostvars = _Site.hostvars.fget(self)
        hostvars['wpveritas_url'] = self.url
        return hostvars


class WpVeritasTestSite(TestSiteTrait, WpVeritasSite):
    WP_VERITAS_SITES_API_URL = 'https://wp-veritas-test.epfl.ch/api/v1/inventory/entries'
    VERIFY_SSL = True


class _LiveSite(_Site):
    @classmethod
    def all(cls):
        logging.debug('Fetching live sites from the %s namespace' % cls.k8s_namespace)
        for path in cls._find_wp_configs():
            site = cls(os.path.dirname(path))
            if site._keep():
                yield site

    @classmethod
    def _find_wp_configs(cls):
        cmd = ['bash', '-c',
               'find %s \( -type d \( %s \) -prune -false \) -o -name wp-config.php' %
               (cls._find_in_dirs, ' '.join(cls._prune_flags()))]
        if not Environment.is_awx():
            cmd = ['oc', 'exec', '-n', cls.k8s_namespace,
                   K8sNamespace(cls.k8s_namespace).get_mgmt_pod_name(), '--'] + cmd

        find = subprocess.Popen(cmd, stdout=subprocess.PIPE, encoding='utf-8')
        while True:
            line = find.stdout.readline()

            if line:
                yield line.rstrip('\n')
            else:
                break

        retcode = find.wait()
        if retcode:
            raise subprocess.CalledProcessError(retcode, cmd)

    _excluded_patterns = ['wp-*', '.git', '*packages', 'jahia-data', 'ansible-backup-*']

    @classmethod
    def _prune_flags(cls):
        return reduce(lambda a,b: a + ['-o'] + b,
                      [['-name', excl] for excl in cls._excluded_patterns])

    def __init__(self, path):
        parsed = re.match(r'/srv/([^/]*)/([^/]*)/htdocs/?(.*?)$', path)
        super(_LiveSite, self).__init__(wwp_env=parsed.group(1),
                                        wp_hostname=parsed.group(2),
                                        wp_path=parsed.group(3))
        self.nfs_path = path

    @property
    def hostvars(self):
        hostvars = _Site.hostvars.fget(self)
        hostvars['nfs_path'] = self.nfs_path
        return hostvars


class LiveTestSite(TestSiteTrait, _LiveSite):
    _find_in_dirs = '/srv/int'


class LiveProductionSite(ProdSiteTrait, _LiveSite):
    _find_in_dirs = '/srv/*/*/htdocs'


class Inventory:
    """Models the entire inventory."""

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
        if site.instance_name in self.inventory['_meta']['hostvars']:
            return   # Duplicate
        self.inventory['_meta']['hostvars'][site.instance_name] = site.hostvars
        self._add_site_to_groups(site)

    def _add_site_to_groups(self, site):
        groups = site.group_hierarchy
        if groups[-1] != 'all_wordpresses':
            groups.append('all_wordpresses')
        for parent, child in pairwise(reversed(groups)):
            self._add_group_to_group(parent, child)
        self._get_group_struct(groups[0]).setdefault('hosts', []).append(site.instance_name)

    def _get_group_struct(self, group_name):
        return self.inventory.setdefault(group_name, {})

    def _add_group_to_group(self, container_name, containee_name):
        children = self._get_group_struct(container_name).setdefault('children', [])
        if containee_name not in children:
            children.append(containee_name)


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


class K8sNamespace:
    _instances = {}
    def __new__(cls, namespace):
        "Singleton constructor - There is only one object instance per value of `namespace`."
        if not namespace in cls._instances:
            cls._instances[namespace] = object.__new__(cls)
            cls._instances[namespace].namespace = namespace
        return cls._instances[namespace]

    @cached
    def get_mgmt_pod_name(self):
        return subprocess.check_output(
                "oc get pods -n %s --no-headers | grep Running |grep mgmt"
                " | head -1 | cut -f1 -d' '" % self.namespace,
                shell=True, encoding='utf-8').rstrip('\n')


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
    def required_inventory_namespaces(cls):
        if cls.is_awx():
            whoami = cls._oc_whoami()
            if 'wwp-test' in whoami:
                return ['wwp-test']
            elif 'wwp' in whoami:  # Also includes the wwp-infra case
                return ['wwp']
            else:
                raise ValueError('Unknown service account %s' % whoami)
        else:
            return os.environ.get('WWP_NAMESPACES', 'wwp-test').split(',')


def pairwise(iterable):
    """s -> (s0,s1), (s1,s2), (s2, s3), ...

    As seen on https://stackoverflow.com/a/5434936/435004
    """
    a, b = itertools.tee(iterable)
    next(b, None)
    return zip(a, b)


if __name__ == '__main__':
    inventory_kinds = os.environ.get('WWP_INVENTORY_SOURCES', 'wpveritas,nfs').split(',')
    inventory_classes = []
    if 'nfs' in inventory_kinds:
        inventory_classes.extend([LiveProductionSite, LiveTestSite])
    # Sites from wp-veritas shadow sites found on NFS with the same .instance_name:
    if 'wpveritas' in inventory_kinds:
        inventory_classes.extend([WpVeritasSite, WpVeritasTestSite])

    sites = []
    for cls in inventory_classes:
        if cls.k8s_namespace in Environment.required_inventory_namespaces():
            sites.extend(cls.all())

    sys.stdout.write(Inventory(sites).to_json())
