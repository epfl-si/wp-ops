Role Name
=========

wordpress-instance — A copy of WordPress (among hundreds) within the EPFL WordPress project

Description
-----------

WordPress at EPFL is served from Kubernetes and Apache and is
comprised of over 700 distinct instances of WordPress. Sites such as
https://inside.epfl.ch/ span multiple WordPress instances, organized
as a tree of sub-directories that reside on an NFS filer and served by
a (containerized) Apache setup based on
[`mod_vhost_alias`](https://httpd.apache.org/docs/2.4/mod/mod_vhost_alias.html).
Sites such as https://www.epfl.ch/ further span multiple Kubernetes
`DeploymentConfig`s (e.g. one for the main site and one for everything
under https://www.epfl.ch/labs/), demultiplexed by URL at the
OpenShift HAProxy.

Within the purview of this role, we abuse the concept of an ansible
“host” a bit to represent each WordPress instance (regardless of which
URL, NFS access path, or `DeploymentConfig` it lives in). Scripts in
`../../inventory/prod` make it so that each of them appears as a
distinct “host” with different variables (e.g. `wp_env`, `wp_path`)
while on the other hand the `ansible_host`, `ansible_port` and
`ansible_user` are mostly always the same. This allows Ansible's
parallelism model to Do The Right Thing, i.e. all operations on all
WordPress sites can run in parallel.

Tasks
-----

See the code and comments in [`tasks/main.yml`](tasks/main.yml) to
find out what this role does on WordPress instances.

License
-------

ISC

Author Information
------------------

ISAS-FSD team <isas-fsd@groupes.epfl.ch>

