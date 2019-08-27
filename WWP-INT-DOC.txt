Feature: wwp-int

This feature allows restoring from backups on a sandbox openshift cluster

PREREQUISITES:
  - python 3 with pyyaml library(for inventory and filters)
  - a working oc client
  - a working ansible installation
  - current-context must be "wwp-int/pub-os-exopge-epfl-ch:443/"*:
	use "oc config current-context" to check the current context
	use "oc config use-context <context_name>" to choose context
	use "oc login" to login to the desired context

USAGE:

  - if wwp-int cluster is empty:
      "./wpsible" will only deploy mgmt with:
       - mount on production backup nas in /backups
       - mount on wwp-int's persistent volume provision system in /srv

  - if mgmt is deployed AND mgmt pod is running (if not, deploy mgmt manually on the OKD console or use "oc rollout latest dc/mgmt"):
      - if respective wordpress servers are NOT deployed:
         "./wpsible" will deploy all httpd deployments only (permission for creating file structure will be denied)
      - if respective wordpress servers ARE deployed:
         "./wpsible" will deploy all httpd deployments AND wordpress instances gathered from /backup mount

      - to limit httpd server deployments :
       "./wpsible -l '<server_name1>, <server_name2>..' " where <server_name#> is of the form httpd-[environment]

      - to limit wordpress instances :

	* "./wpsible -l '<instance_name1>, <instance_name2> ...' " where <instance_name#> is the name of the backup 
	  folder for the specific instance (fetched from /backups)
		example: 
			./wpsible -l  _srv_www_www.epfl.ch_htdocs
			./wpsible -l '_srv_www_www.epfl.ch_htdocs, _srv_www_www.epfl.ch_htdocs_about'


	* "./wpsible -l '<environment1>, ...' " where <environment1> is the name of the group of wordpress instances
		example: 
			./wpsible -l httpd-www
			./wpsible -l 'httpd-www, httpd-inside'

	* edit the python dynamic inventory ansible/inventory/wp-int/wordpress-instances:
	  - call generate_inventory(sorted= True, limit=0, max_depth=-1) (bottom of the file)
	    "sorted" will sort instances by file depth, 
	    "limit" will truncate instance lists in each group until the specified number. A value of 0 will not limit instances number 
	    "max_depth" will filter instances by file depth. A depth strictly smaller than 0 will not filter instances, 0 yields root 
	     wordpress directories only, ect.

   - to get an inventory listing for a given dynamic inventory:
      structured:
        ansible-inventory -i <inventory_script> --graph
      full variable listing:
        ansible-inventory -i <inventory_script> --list
  