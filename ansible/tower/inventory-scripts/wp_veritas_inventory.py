#!/usr/bin/env python

# All rights reserved. ECOLE POLYTECHNIQUE FEDERALE DE LAUSANNE, Switzerland, VPSI, 2019
#
# Wp-vertias API fetcher, to build a JSON ansible inventory
# this file is currently saved into https://gist.github.com/jdelasoie/1ea9a69d7f5b5fbb9fb24422fe862dee as a remote source inventory
#
# Example invocation:
#    wp-veritas-inventory.py --list

import argparse
import os.path
import sys
import logging


import json
import yaml

import requests
from six.moves.urllib.parse import urlparse, quote

from StringIO import StringIO


WP_VERITAS_SITES_API_URL = 'https://wp-veritas.epfl.ch/api/v1/sites/'

OC_API_URL = 'https://pub-os-exopge.epfl.ch/api/v1/'
OC_PROJECT_NAME = 'wwp'
OC_KEY_FILE = '/run/secrets/kubernetes.io/serviceaccount/token'


def _fetch_wp_veritas():
    logging.debug('Fetching sites from  ' + WP_VERITAS_SITES_API_URL)
    r = requests.get(WP_VERITAS_SITES_API_URL)

    if not r.ok:
        r.raise_for_status()

    return r.json()


# path on disk is not a provided data, so we have to build it
def _build_path(site):
    site_path = '/srv/' + site['openshiftEnv'] + '/' + site['parsed_url'].netloc + '/htdocs' + site['parsed_url'].path
    return site_path


def _build_name(site):
    path = site['parsed_url'].path
    # dont override groups name with hosts name
    #labs are in www, it's a special case
    if site['openshiftEnv'] == 'labs':
        site_name = path
    else:
        site_name = site['openshiftEnv'] + path

    # always clear site_name last separator
    site_name = (site_name[:1] if site_name.endswith('/') else site_name)
    if not site_name.startswith('/'):
        site_name = '/' + site_name

    return site_name


def _fetch_oc_for_info(pod_name):
    token = ""

    with open(OC_KEY_FILE) as token_file:
        token = token_file.read()

    if token == "":
        raise Exception("Can't read the OC token on %s" % OC_KEY_FILE)
    else:
        token = 'Bearer ' + token

    url = OC_API_URL + 'namespaces/' + OC_PROJECT_NAME + '/pods'

    # add selector
    url += '?labelSelector=' + quote("app in (httpd-%s)" % pod_name)
    #url += '?labelSelector=' + quote("app in (httpd-gcharmier)") + '&fieldSelector=' + quote("status.phase=Running")

    logging.debug('Fetching OC pods list from ' + url)
    headers = {'Authorization': token}

    r = requests.get(url, headers=headers, verify=True)

    if not r.ok:
        r.raise_for_status()

    return r.json()


# Add static data about group vars, if we any instance in it
def fullfil_pod_structure(inventory_dict):
    for key in inventory_dict.keys():
        if key == '_meta':
            # ignore _meta, this is not a pod, only an ansible key
            continue

        oc_data = _fetch_oc_for_info(key)  # request data from OC
        if oc_data['items']:
            ansible_oc_pod = ""
            for item in oc_data['items']:
                if 'name' in item['metadata'] and item['metadata']['name']:
                    ansible_oc_pod = item['metadata']['name']
                    # retrieve only a pod name, not all
                    continue

            logging.debug("ansible pod found %s for %s" % (ansible_oc_pod, key))

            inventory_dict[key]['vars'] = {
                "wp_hostname": "www.epfl.ch",
                "ansible_connection": "oc",
                "ansible_oc_pod": ansible_oc_pod,
                "ansible_oc_namespace": key,
                "ansible_oc_container": "httpd-" + key,

                # TODO:? may need oc_token (should be added in Vault) or oc_key_file
                # 'oc_host'
                }
        else:
            logging.warning('Pods httpd-%s does not exist into the OC project %s' % (key, OC_PROJECT_NAME))

    return inventory_dict


def print_list():
    inventory = {
        '_meta': {'hostvars': {}}
    }

    for site in _fetch_wp_veritas():
        # filter entries :
        # we only work with created sites that have the data we need
        # unmanaged are not in our scope
        # no url = not for AWX
        # no env = not for AWX
        # and explicitly ignored env
        if site['status'] != 'created' or \
           site['type'] == 'unmanaged' or \
           site['url'] == '' or \
           site['openshiftEnv'] == '' or \
           site['openshiftEnv'] == 'manager' or \
           site['openshiftEnv'] == 'subdomains':
            continue

        # add parsed_url, we will need it
        site['parsed_url'] = urlparse(site['url'])

        host_name = _build_name(site)

        # fullfil vars for the site
        meta_site = {
            "wp_veritas_url": 'https://wp-veritas.epfl.ch/edit/' + site['_id'],
            "url": site['url'],
            "tagline": site['tagline'],
            "title": site['title'],
            "openshift_env": site['openshiftEnv'],
            "category": site['category'],
            "theme": site['theme'],
            "faculty": site['faculty'],
            "languages": site['languages'],
            "unit_id": site['unitId'],
            "wp_path": _build_path(site),
        }

        inventory.setdefault(site['openshiftEnv'], {}).setdefault('hosts', []).append(host_name)
        inventory['_meta']['hostvars'][host_name] = meta_site

    inventory = fullfil_pod_structure(inventory)

    io = StringIO()
    json.dump(inventory, io, indent=2)
    return io.getvalue()

# don't use host, but the fulllist, for optimal process
def print_host(host):
    return {}    


def get_args(args_list):
    parser = argparse.ArgumentParser(
        description='ansible inventory script parsing')
    mutex_group = parser.add_mutually_exclusive_group(required=True)
    help_list = 'list all hosts from .ssh/config inventory'
    mutex_group.add_argument('--list', action='store_true', help=help_list)
    help_host = 'display variables for a host'
    mutex_group.add_argument('--host', help=help_host)
    return parser.parse_args(args_list)


def main(args_list):
    args = get_args(args_list)
    if args.list:
        return sys.stdout.write(print_list())
    if args.host:
        return print_host(args.host)

if __name__ == '__main__':
    main(sys.argv[1:])
