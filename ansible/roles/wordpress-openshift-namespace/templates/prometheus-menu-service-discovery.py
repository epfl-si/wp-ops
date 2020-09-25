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

    @property
    def targets(self):
        # Only return wp sites that are managed and that are hosted on the OpenShift infra (aka ours wordpresses)
        return [{"targets": [s['url'] for s in (s for s in self.sites if (s['wpInfra'] and not s['openshiftEnv'].startswith('unm')))]}]

    def to_json(self):
        return json.dumps(self.targets)

while True:
    try:
        targets_json = DynamicConfig().to_json()
        with open("/prometheus-config/dynamic/targets.json", "w") as f:
            f.write(targets_json)
    except:  # noqa
        logging.error(traceback.format_exc())
    time.sleep(60)
