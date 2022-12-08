<h1 align="center">
  WordPress @ EPFL: DevOps Boogaloo
</h1>

[![Build Status](https://travis-ci.com/epfl-si/wp-ops.svg?branch=master)](https://app.travis-ci.com/github/epfl-si/wp-ops)

In this repository you will find:

- The Dockerfiles and build dependencies for all custom-made Docker images

- Some Ansible code to manage state on-disk and inside the Kubernetes data store

# Prerequisites and Tools

## OpenShift

1. [Install the OpenShift command-line tools]
1. Browse https://pub-os-exopge.epfl.ch/ and log in using your GASPAR credentials
1. From the “you” menu in the top right, select Copy Login Command
1. Paste into a terminal window
1. Check your access, e.g. <pre>oc get pods -n wwp-test</pre>

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

<!-- start_contributors mode:bubble -->
![@LuluTchab avatar](https://images.weserv.nl/?url=https://avatars.githubusercontent.com/u/11942430?v=4&h=84&w=84&fit=cover&mask=circle&maxage=7d)
![@ebreton avatar](https://images.weserv.nl/?url=https://avatars.githubusercontent.com/u/490665?v=4&h=84&w=84&fit=cover&mask=circle&maxage=7d)
![@GregLeBarbar avatar](https://images.weserv.nl/?url=https://avatars.githubusercontent.com/u/4997224?v=4&h=84&w=84&fit=cover&mask=circle&maxage=7d)
![@domq avatar](https://images.weserv.nl/?url=https://avatars.githubusercontent.com/u/1629585?v=4&h=84&w=84&fit=cover&mask=circle&maxage=7d)
![@jdelasoie avatar](https://images.weserv.nl/?url=https://avatars.githubusercontent.com/u/15261020?v=4&h=84&w=84&fit=cover&mask=circle&maxage=7d)
![@ponsfrilus avatar](https://images.weserv.nl/?url=https://avatars.githubusercontent.com/u/176002?v=4&h=84&w=84&fit=cover&mask=circle&maxage=7d)
![@MarceloMuriel avatar](https://images.weserv.nl/?url=https://avatars.githubusercontent.com/u/4720032?v=4&h=84&w=84&fit=cover&mask=circle&maxage=7d)
![@alinekeller avatar](https://images.weserv.nl/?url=https://avatars.githubusercontent.com/u/6631947?v=4&h=84&w=84&fit=cover&mask=circle&maxage=7d)
![@lvenries avatar](https://images.weserv.nl/?url=https://avatars.githubusercontent.com/u/29034311?v=4&h=84&w=84&fit=cover&mask=circle&maxage=7d)
![@lboatto avatar](https://images.weserv.nl/?url=https://avatars.githubusercontent.com/u/25363740?v=4&h=84&w=84&fit=cover&mask=circle&maxage=7d)
![@cburki avatar](https://images.weserv.nl/?url=https://avatars.githubusercontent.com/u/7870123?v=4&h=84&w=84&fit=cover&mask=circle&maxage=7d)
![@zuzu59 avatar](https://images.weserv.nl/?url=https://avatars.githubusercontent.com/u/15345233?v=4&h=84&w=84&fit=cover&mask=circle&maxage=7d)
![@dabelenda avatar](https://images.weserv.nl/?url=https://avatars.githubusercontent.com/u/17007649?v=4&h=84&w=84&fit=cover&mask=circle&maxage=7d)
![@jaepetto avatar](https://images.weserv.nl/?url=https://avatars.githubusercontent.com/u/2668031?v=4&h=84&w=84&fit=cover&mask=circle&maxage=7d)
![@williambelle avatar](https://images.weserv.nl/?url=https://avatars.githubusercontent.com/u/2843501?v=4&h=84&w=84&fit=cover&mask=circle&maxage=7d)
![@multiscan avatar](https://images.weserv.nl/?url=https://avatars.githubusercontent.com/u/12849?v=4&h=84&w=84&fit=cover&mask=circle&maxage=7d)
![@JGodin-C2C avatar](https://images.weserv.nl/?url=https://avatars.githubusercontent.com/u/40758407?v=4&h=84&w=84&fit=cover&mask=circle&maxage=7d)
![@obieler avatar](https://images.weserv.nl/?url=https://avatars.githubusercontent.com/u/24526380?v=4&h=84&w=84&fit=cover&mask=circle&maxage=7d)
<!-- end_contributors -->


[access to the test and/or production infrastructure]: https://sico.epfl.ch:8443/
[Install Ansible]: https://docs.ansible.com/ansible/latest/installation_guide/intro_installation.html
[Install the OpenShift command-line tools]: https://docs.openshift.com/container-platform/3.11/cli_reference/get_started_cli.html#installing-the-cli
[Install Keybase]: https://keybase.io/download

# File Layout

This module comprises the following subdirectories:

- `ansible`: All the support for Ansible and Ansible Tower. Theoretically, `ansible/wpsible` can bring up the entire serving infrastructure from a backup into an empty OpenShift namespace that the operator has `oc login` access to — Including all required Kubernetes objects. A subset of the Ansible tasks is managed by Ansible Tower, providing a dashboard and crontab-like functionality to the operator. See `ansible/README.md` for further details on the layout inside this directory.
- `docker`: Dockerfiles used to build the production images (also used by [wp-dev](https://github.com/epfl-si/wp-dev) to build the images on your workstation)
- `Makefile` and `k8s-backup`: manage the archiving of select mutable pieces of the Kubernetes configuration into a Keybase-encrypted git
