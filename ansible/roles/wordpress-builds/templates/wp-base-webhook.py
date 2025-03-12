#!/usr/bin/env python3

from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os
import re
import requests
import subprocess
import sys
from types import SimpleNamespace


class TektonableBranch:
    @classmethod
    def maybe_create_new (cls, trigger):
        """If `trigger` is a pull request creation, make and persist a new `TektonableBranch` instance to Kubernetes."""
        pass  # TODO: eliminate the "refs/heads" prefix; create Kubernetes object; start its build immediately

    @classmethod
    def all (cls):
        # TODO: enumerate existing branches out of the Kubernetes state.
        return [ cls(branch="WPN") ]

    def __init__ (self, branch):
        self.branch = branch
        self.quay = QuayRequests()
        self.quay_organization = "svc0041"

    @property
    def sbom (self):
        class SBOM:
            # TODO: load state from a Kubernetes object

            @classmethod
            def uses (cls, repo, ref):
                """True iff the previous build of this branch used branch `ref` of `repo`."""
                return True   # TODO: filter! This will rebuild everything everywhere all at once.

        return SBOM

    def rebuild (self):
        print(f"TODO: rebuild for {self.next_build_tag} on {self.branch}", file=sys.stderr)

    @property
    def next_build_tag (self):
        this_year = datetime.today().strftime("%Y")
        return f"{this_year}{self.branch_midfix}-{'%03d' % self.next_build_id}"


    @property
    def next_build_id (self):
        return 1 + max((
            self._get_max_of_build_ids("wp-nginx"),
            self._get_max_of_build_ids("wp-php")))


    def _get_all_tags (self, image_name):
        return self.quay.get(f"/api/v1/repository/{self.quay_organization}/{image_name}").json()["tags"].keys()

    def _get_max_of_build_ids (self, image_name):
        def parse (image_tag):
            return re.match(r"(?P<year>\d+)-(?P<midfix>.*-)?(?P<serial>\d+)$", image_tag)

        parsed = [parse(p) for p in self._get_all_tags(image_name)]

        return max(int(p["serial"]) for p in parsed if p and not p["midfix"])

    @property
    def branch_midfix (self):
        if self.branch == "WPN":
            return ""
        else:
            branch_moniker = self.branch.lower()
            branch_moniker = re.sub('([^a-z0-9]+)', '-', branch_moniker)
            return f"-{branch_moniker}"


class WebhookHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        payload = json.loads(post_data, object_hook=lambda d: SimpleNamespace(**d))

        print(payload, file=sys.stderr)
        print(f"Build triggered from {payload.repository.full_name} on {payload.ref}",
              file=sys.stderr)

        # TODO: create a k8s "Tekton" Tasks to rebuild every wp-base
        for b in TektonableBranch.all():
            if b.sbom.uses(repo=payload.repository.full_name, ref=payload.ref):
                b.rebuild()

        if payload.repository.full_name == "epfl-si/wp-base":
            TektonableBranch.maybe_create_new(payload)

        self.send_response(200)
        self.end_headers()

class QuayRequests:
    def __init__ (self):
        self.url_base = f"https://{os.getenv('QUAY_API_HOSTNAME')}"
        self.bearer_token = os.getenv('QUAY_API_BEARER_TOKEN')

    def request (self, method, endpoint, json, headers={}):
        if "Authorization" not in headers:
            headers["Authorization"] = f"bearer {self.bearer_token}"
        response = requests.request(
            method,
            f"{self.url_base}{endpoint}",
            json=json, headers=headers)

        response.raise_for_status()
        return response

    def get (self, endpoint, json=None, headers={}):
        return self.request("GET", endpoint, json, headers)

    def post (self, endpoint, json, headers={}):
        return self.request("POST", endpoint, json, headers)

    def put (self, endpoint, json, headers={}):
        return self.request("PUT", endpoint, json, headers)

    def delete (self, endpoint, json=None, headers={}):
        return self.request("DELETE", endpoint, json, headers)


server = HTTPServer(('', 8080), WebhookHandler)
server.serve_forever()
