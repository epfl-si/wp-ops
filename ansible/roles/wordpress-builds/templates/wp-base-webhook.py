#!/usr/bin/env python3

from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import subprocess
import sys
from types import SimpleNamespace


class WebhookHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        payload = json.loads(post_data, object_hook=lambda d: SimpleNamespace(**d))

        print(payload, file=sys.stderr)
        print(f"Build triggered from {payload.repository.full_name} on {payload.ref}",
              file=sys.stderr)

        # TODO: create a k8s "Tekton" Tasks to rebuild every wp-base

        self.send_response(200)
        self.end_headers()

server = HTTPServer(('', 8080), WebhookHandler)
server.serve_forever()
