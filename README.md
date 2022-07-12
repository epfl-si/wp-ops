<h1 align="center">
  WordPress @ EPFL: DevOps Boogaloo
</h1>

[![Build Status](https://travis-ci.com/epfl-si/wp-ops.svg?branch=master)](https://app.travis-ci.com/github/epfl-si/wp-ops)

In this repository you will find:

- The Dockerfiles and build dependencies for all custom-made Docker images

- Some Ansible code to manage state on-disk and inside the etcd store

# Prerequisites and Tools

## OpenShift

[Install the OpenShift command-line tools] and verify that you have access, e.g. <pre>
oc login
oc get pods -n wwp-test
</pre>

## Ansible

[Install Ansible] and familiarize yourself with how it works.

## Keybase and eyaml

These are required to (re)deploy QA and production secrets.

💡 You can get a lot of mileage out of Ansible and OpenShift even if
you *do not* have access to the Keybase teams. In that case,
feel free to skip this section.

1. Install eyaml with<pre>gem install hiera-eyaml</pre>
1. [Install Keybase] and create an account for yourself
1. Obtain membership in the relevant Keybase teams

# Operations

To be documented

[access to the test and/or production infrastructure]: https://sico.epfl.ch:8443/
[Install Ansible]: https://docs.ansible.com/ansible/latest/installation_guide/intro_installation.html
[Install the OpenShift command-line tools]: https://docs.openshift.com/container-platform/3.11/cli_reference/get_started_cli.html#installing-the-cli
[Install Keybase]: https://keybase.io/download

# File Layout

This module comprises the following subdirectories:

- `ansible`: All the support for Ansible and Ansible Tower. Theoretically, `ansible/wpsible` can bring up the entire serving infrastructure from a backup into an empty OpenShift namespace that the operator has `oc login` access to — Including all required Kubernetes objects. A subset of the Ansible tasks is managed by Ansible Tower, providing a dashboard and crontab-like functionality to the operator. See `ansible/README.md` for further details on the layout inside this directory.
- `docker`: Dockerfiles used to build the production images (also used by [wp-dev](https://github.com/epfl-si/wp-dev) to build the images on your workstation)
- `Makefile` and `k8s-backup`: manage the archiving of select mutable pieces of the Kubernetes configuration into a Keybase-encrypted git
