<h1 align="center">
  WordPress @ EPFL: DevOps Boogaloo
</h1>

[![Build Status](https://travis-ci.org/epfl-si/wp-ops.svg?branch=master)](https://travis-ci.org/epfl-si/wp-ops)

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

# Contributor list

Big up to all the following people, without whom this project will not be

| [<img src="https://avatars0.githubusercontent.com/u/490665?v=4s=100" width="100px;"/><br /><sub>Manu B.</sub>](https://github.com/ebreton)<br /> | [<img src="https://avatars0.githubusercontent.com/u/2668031?v=4s=100" width="100px;"/><br /><sub>Manu J. </sub>](https://github.com/jaepetto)<br /> | [<img src="https://avatars0.githubusercontent.com/u/4997224?v=4s=100" width="100px;"/><br /><sub>Greg</sub>](https://github.com/GregLeBarbar)<br /> | [<img src="https://avatars0.githubusercontent.com/u/11942430?v=4s=100" width="100px;"/><br /><sub>Lulu</sub>](https://github.com/LuluTchab)<br /> | [<img src="https://avatars0.githubusercontent.com/u/25363740?v=4s=100" width="100px;"/><br /><sub>Laurent</sub>](https://github.com/lboatto)<br /> | [<img src="https://avatars0.githubusercontent.com/u/29034311?v=4s=100" width="100px;"/><br /><sub>Luc</sub>](https://github.com/lvenries)<br /> | <br /> |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| [<img src="https://avatars0.githubusercontent.com/u/1629585?v=4s=100" width="100px;"/><br /><sub>Dominique</sub>](https://github.com/domq)<br /> | [<img src="https://avatars0.githubusercontent.com/u/176002?v=4s=100" width="100px;"/><br /><sub>Nicolas </sub>](https://github.com/ponsfrilus)<br /> | [<img src="https://avatars0.githubusercontent.com/u/2843501?v=4s=100" width="100px;"/><br /><sub>William </sub>](https://github.com/williambelle)<br /> | [<img src="https://avatars0.githubusercontent.com/u/28109?v=4s=100" width="100px;"/><br /><sub>CampToCamp</sub>](https://github.com/camptocamp)<br /> | <br /> | <br /> | | <br /> | <br /> |


[access to the test and/or production infrastructure]: https://sico.epfl.ch:8443/
[Install Ansible]: https://docs.ansible.com/ansible/latest/installation_guide/intro_installation.html
[Install the OpenShift command-line tools]: https://docs.openshift.com/container-platform/3.11/cli_reference/get_started_cli.html#installing-the-cli
[Install Keybase]: https://keybase.io/download

# File Layout

This module comprises the following subdirectories:

- `ansible`: All the support for Ansible and Ansible Tower. Theoretically, `ansible/wpsible` can bring up the entire serving infrastructure from a backup into an empty OpenShift namespace that the operator has `oc login` access to — Including all required Kubernetes objects. A subset of the Ansible tasks is managed by Ansible Tower, providing a dashboard and crontab-like functionality to the operator. See `ansible/README.md` for further details on the layout inside this directory.
- `docker`: Dockerfiles used to build the production images (also used by [wp-dev](https://github.com/epfl-si/wp-dev) to build the images on your workstation)
- `Makefile` and `k8s-backup`: manage the archiving of select mutable pieces of the Kubernetes configuration into a Keybase-encrypted git
