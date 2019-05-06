#!/usr/bin/env python3
# -*- coding:utf-8 -*-

from flask import Flask, request
import sys
from probe import probe
from prometheus import Metrics


app = Flask(__name__)


@app.route('/wpmenuprobe')
def route_probe():
    target = request.args['target']
    metrics = Metrics()
    probe(target, metrics)
    return metrics.as_flask_response()


argv = sys.argv.copy()

if len(argv) > 0 and argv[0].endswith(".py"):
    argv.pop(0)

if len(argv) == 0:
    app.run(host='0.0.0.0', port=8080, debug=True)
else:
    from cachier import cachier
    import requests

    @cachier()
    def get_json(url):
        return requests.get(url).json()

    metrics = Metrics()
    probe(argv[0], metrics, inject_get_json=get_json)
    print(metrics)
