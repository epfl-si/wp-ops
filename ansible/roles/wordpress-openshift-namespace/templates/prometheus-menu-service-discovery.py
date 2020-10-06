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
from datetime import datetime

class DynamicConfig:

    targetPath = "/prometheus-config/dynamic/targets.json"

    def __init__(self, url="https://wp-veritas.epfl.ch/api/v1/sites", targetPath=None, frequency=60):
        self.url = url
        if targetPath:
            self.targetPath = targetPath
        else:
            self.targetPath = DynamicConfig.targetPath
        self.frequency = frequency
        print(f"{datetime.now().isoformat()} Configurator started !"
              f"\n\t - url: {self.url}"
              f"\n\t - dynamic file: {self.targetPath}"
              f"\n\t - frequency: {self.frequency}s",
            flush=True)

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
        targets_by_wp_env = {}
        for s in self.sites:
            if not s['wpInfra']:
                continue
            wp_env = s['openshiftEnv']
            if wp_env.startswith('unm'):
                continue

            url = s['url'] if s['url'].endswith('/') else s['url'] + '/'
            targets_by_wp_env.setdefault(wp_env, []).append(url)
        return targets_by_wp_env.items()

    def _write(self, struct):
        tmpTarget = self.targetPath + '.tmp'
        with open(tmpTarget, "w") as f:
            f.write(json.dumps(struct))
        os.rename(tmpTarget, self.targetPath)

    def write_targets(self):
        self._write([
                dict(
                    targets=targets,
                    labels=dict(wp_env=wp_env))
                for wp_env, targets in self.enumerate()])

dc = DynamicConfig()
while True:
    try:
        dc.write_targets()
    except:  # noqa
        logging.error(traceback.format_exc())
    time.sleep(dc.frequency)
