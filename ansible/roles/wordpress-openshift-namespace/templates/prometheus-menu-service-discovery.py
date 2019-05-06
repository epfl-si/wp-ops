"""Automatically compute targets for the production WordPress Prometheus.

Every 60 seconds, enumerate Web sites in wp-veritas and produce a number
of dynamic targets for it.
"""

import logging
import time
import traceback


class Targets:
    def to_json(self):
        return '{}'


while True:
    try:
        targets_json = Targets().to_json()
        with open("/prometheus-config/dynamic/targets.json", "w") as f:
            f.write(targets_json)
    except:
        logging.error(traceback.format_exc())
    time.sleep(60)
