#!/usr/bin/env python3

from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
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
        return 42   # TODO: fetch and increment from Kubernetes or Quay state

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

server = HTTPServer(('', 8080), WebhookHandler)
server.serve_forever()
