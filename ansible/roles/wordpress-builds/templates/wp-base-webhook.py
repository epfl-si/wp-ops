#!/usr/bin/env python3

import json
import subprocess
import sys

from http.server import BaseHTTPRequestHandler, HTTPServer


class WebhookHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        payload = json.loads(post_data)

        print(post_data, file=sys.stderr)

        self.send_response(200)
        self.end_headers()

server = HTTPServer(('', 8080), WebhookHandler)
server.serve_forever()
