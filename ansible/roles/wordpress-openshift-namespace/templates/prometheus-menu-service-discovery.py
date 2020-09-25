"""Automatically compute targets for the production WordPress Prometheus.

Every 60 seconds, enumerate Web sites in wp-veritas and produce a number
of dynamic targets for it.
"""

import json
import logging
import os
import time
import traceback
import urllib.request


class DynamicConfig:
    def __init__(self, url="https://wp-veritas.epfl.ch/api/v1/sites"):
        self.url = url

    def _get_json(self):
        if 'HOME' in os.environ:
            TEST_SITES_JSON = os.environ['HOME'] + "/Dev/WordPress/tmp/sites"
            if os.path.exists(TEST_SITES_JSON):
                return open(TEST_SITES_JSON).read()

        res = urllib.request.urlopen(self.url)
        return ''.join(res.read().decode("utf-8"))

    @property
    def sites(self):
        if not hasattr(self, '_sites'):
            self._sites = json.loads(self._get_json())
        return self._sites

    def enumerate(self):
        targets_by_env = {}
        for s in self.sites:
            if not s['wpInfra']:
                continue
            env = s['openshiftEnv']
            if env.startswith('unm'):
                continue

            url = s['url']
            targets_by_env.setdefault(env, []).append(url)
        return targets_by_env.items()

while True:
    try:
        with open("/prometheus-config/dynamic/targets.json", "w") as f:
            f.write(json.dumps([
                dict(
                    targets=targets,
                    labels=dict(env=env))
                for env, targets in DynamicConfig().enumerate()]))
    except:  # noqa
        logging.error(traceback.format_exc())
    time.sleep(60)
