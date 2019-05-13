#!/usr/bin/env python

# All rights reserved. ECOLE POLYTECHNIQUE FEDERALE DE LAUSANNE, Switzerland, VPSI, 2019
#
# Wp-vertias API fetcher, to build a JSON ansible inventory
#
# Example invocation:
#    wp-veritas-inventory.py --list

import argparse
import os.path
import sys

import json
import yaml

import requests
from six.moves.urllib.parse import urlparse

from StringIO import StringIO


WP_VERITAS_SITES_API_URL = 'https://wp-veritas.epfl.ch/api/v1/sites'



def _fetch_wp_veritas():
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


# Add static data about group vars, if we any instance in it
def fullfil_pod_structure(inventory_dict):
    if 'www' in inventory_dict.keys():
        inventory_dict['www']['vars'] = {
            "wp_env": "www",
            "wp_hostname": "www.epfl.ch",
            "ansible_connection": "oc",
            "ansible_oc_pod": "httpd-www-32-6n7f6",
            "ansible_oc_namespace": "wwp",
            "ansible_oc_container": "httpd-www",
        }

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
            "opneshift_env": site['openshiftEnv'],
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
