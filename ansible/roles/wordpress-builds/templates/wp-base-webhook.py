#!/usr/bin/env python3

from http.server import BaseHTTPRequestHandler, HTTPServer
import json, subprocess

class WebhookHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        payload = json.loads(post_data)
        branch = payload.get('branch', 'unknown')
        pr_number = payload.get('pr', '')

        tekton_name = f"build-{branch}" if not pr_number else f"build-PR{pr_number}"
        subprocess.run([
            "kubectl", "create", "pipelinerun", tekton_name,
            "--from=pipeline/wp-base",
            "--param=repo-url=" + payload["repository"],
            "--param=branch-name=" + branch
        ])

        self.send_response(200)
        self.end_headers()

server = HTTPServer(('', 8080), WebhookHandler)
server.serve_forever()
