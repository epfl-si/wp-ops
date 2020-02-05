# Temporary documentation about how to utilize ssh or oc connector for the restore-from-prod task set
Targeted tasks by the connector: 
    wp-ops/ansible/inventory/wp-int/wordpress-instances
    wp-ops/ansible/roles/wordpress-instance/tasks/restore-from-prod.yml

Prerequisits:
    logged in oc on project "wp-int"
    running mgmt pod on project "wp-int"
    running desired httpd pod for the desired restores on project "wp-int"
    export mgmt ssh port to desired local port:
        `oc port-forward -n wp-int <mgmt_pod_name> <local_port>:22`
    change `port` variable in wp-ops/ansible/inventory/wp-int/wordpress-instances to be equal to `<local_port>` (default local port is 2222)

Usage:
    ```
    cd wp-ops/ansible
    ./wpsible -l <group> --connector <connector>
    ```
    where <connector> is either `ssh` or `oc`
    `--connector` option is *not* optional for this inventory and is *ignored* for other inventories
