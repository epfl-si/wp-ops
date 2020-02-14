#Minishift deployment documentation

#GOAL :

Deploy an openshift infrastructure using a local minishift cluster that is as identical as possible 
to the production's infrastructure:
- one management 'mgmt' pod mounted on a file system share provided by the user
- as many httpd pods as the inventory mentions, see `wp-ops/ansible/inventory/minishift/wordpress-deployments`
- all pods are using images from the production environnement

#Prerequisites:

- keybase's team folder mounted on `/keybase/team` on the ansible machine.
- docker installation on the ansible machine:
   - add the current user to the sudoers group of docker in /etc/group
- working oc installation on the ansible machine
- functional nas and sql servers serving on the ansible machine's public IP, and ports 2049 and 3306 respectively
   - you can clone `git@github.com:epfl-sdf/tests_infra_persitent.git` and follow the instructions to run the nas and sql containers
   - you will also need to create an `srv` folder at the root of the nfs server (in `nfs-share/` if you follow the git repo mentionned above)
       > `mkdir nfs-share/srv; sudo chown www-data:www-data srv` 
- minishift installation:
   - use `minishift start` to deploy the cluster. On windows, you might need to run (on an admin powershell) `minishift --username usr --password pass start`
   where `usr` and `pass` are the current user's credentials.
   - The cluster should be routed to an IP similar to 192.168.99.* , the current project must be `myproject`, and the openshift user should be `developer`
   if the routing is different, you can change `wp-ops/ansible/wpsible` accordingly
- having the login token for `https://pub-os-exopge.epfl.ch/console/` present in ~/.kube/config:
   - you can do so by logging into `https://pub-os-exopge.epfl.ch/console/` using `oc`, then log into your minishift cluster again.

#Usage:

- Run `./wpsible -t check` to setup your minishift environnement correctly.
	this will do things such as checking minishift's dns resolver, giving correct cluster rights to `developer`, and checking the `pub-os-exopge.epfl.ch` credentials agains epfl's docker registry
- Run `./wpsible` to deploy the infrastructure. This will:
   - setup Persistent volumes to the nas and secrets holding the credentials to the sql server
   - create image streams using the production's images and pulling the images into the local cluster
   - setting up volumes and deployments.
   /!\ at the task "Prepare nfs files", the playbook may fail if the mgmt pod takes too long to deploy. If it does you can just wait for it to be ready, then running `./wpsible` again

The httpd pods should be mounted to their respective subpaths, mgmt should be mounted to srv and has access to all subpaths

          