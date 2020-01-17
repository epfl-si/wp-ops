#!/usr/bin/python3
import subprocess
import shlex
import json
import re


targets = [{ 
            'ssh_port': '32222',
            'ssh_user': 'www-data',
            'ssh_host': 'ssh-wwp.epfl.ch',
            'remote_path': '/srv/*/*/htdocs'
            }]

class WPInventory():

    def __init__(self, targets):

        self.nicknames_already_taken = []
        self.wordpresses = {}

        for target in targets:
            for wordpress_instance in self.collect_wordpress_installs_over_ssh(target):
                wordpress_instance = {**target, **wordpress_instance}
                category = self.categorize(wordpress_instance)
                
                if category not in self.wordpresses:
                    self.wordpresses[category] = []
                
                self.wordpresses[category].append(wordpress_instance)

        self.as_ansible_struct()

    def categorize(self, wordpress_instance):
        """
        Determines which Ansible group a given Wordpress goes into
        """
        wp_env = wordpress_instance['wp_env']

        if wp_env == 'form':
            cat_nickname = 'formation'
        elif wp_env.startswith('unm-'):
            cat_nickname = 'unmanaged'
        else:
            cat_nickname = wp_env

        return "prod-{}".format(cat_nickname)


    def collect_wordpress_installs_over_ssh(self, target_dict):

        cmd_to_exec = "find {} \( -type d \( -name wp-* -o -name .git -o -name *packages -o -name ansible-backup-* \) -prune -false -o -name wp-config.php \)".format(target_dict['remote_path'])

        ssh_cmd = 'ssh -xT -q -p {} -o StrictHostKeyChecking=no {}@{} "{}"'.format(target_dict['ssh_port'],
                                                                        target_dict['ssh_user'],
                                                                        target_dict['ssh_host'],
                                                                        cmd_to_exec)
        args = shlex.split(ssh_cmd)
        ssh =  subprocess.Popen(args, 
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                shell=False)

        result = ssh.stdout.readlines()
        if result == []:
            error = ssh.stderr.readlines()
            raise ValueError("ERROR: {}".format(error))

        retval = []

        for line in result:
            line = line.decode().strip()
            values = re.findall(r'/srv/([^/]*)/([^/]*)/htdocs/(.*?)/?wp-config.php$', line)

            if values:
                retval.append({'wp_env': values[0][0],
                                'wp_hostname': values[0][1],
                                'wp_path': values[0][2]})
            else:
                raise ValueError("Bizarre in line {}".format(line))

        return retval


    def as_ansible_struct(self):
        # https://docs.ansible.com/ansible/latest/dev_guide/developing_inventory.html

        self.ansible_struct = {'all-wordpresses': { 'children': [ 'prod-wordpresses' ] },
                                '_meta': { 'hostvars': {} } }

        for category  in self.wordpresses:
            for wp in self.wordpresses[category]:

                wp = self.as_ansible_hostvars(wp)

                nickname = self.nickname(wp)

                if category not in self.ansible_struct:
                    self.ansible_struct[category] = {'hosts': []}
                
                self.ansible_struct[category]['hosts'].append(nickname)

                self.ansible_struct['_meta']['hostvars'][nickname] = wp
        
        # Adding all categories as children
        self.ansible_struct['prod-wordpresses'] = { 'children': list(self.wordpresses.keys())}

    
    def as_ansible_hostvars(self, wp):
        retval = {
            'ansible_python_interpreter': '/usr/bin/python3',
            'openshift_namespace': 'wwp-prod',
            'wp_ensure_symlink_version': '5.2'
        }
        
        for key, val in wp.items():
            if re.match(r'^(ssh|wp|ansible)_', key):
                key = re.sub(r'^ssh_', 'ansible_', key)
                retval[key] = val if val is not None else ''

        return retval


    def nickname(self, wp):
        hostname = wp['wp_hostname']
        path = wp['wp_path']

        hostname = re.sub(r'\Wepfl\.ch$', '', hostname)
        hostname = re.sub(r'\W', '-', hostname)

        if path == "":
            steam = hostname
        else:
            path = re.sub(r'\/$', '', path)
            path = re.sub(r'\/', '-', path)
            steam = "{}-{}".format(hostname, path)
        
        uniq = 0
        nickname = steam

        # We unsure to have a uniq nickname for WP instance
        while nickname in self.nicknames_already_taken:
            uniq += 1
            nickname = "{}{}".format(steam, uniq)
        
        self.nicknames_already_taken.append(nickname)

        return nickname


    def get_inventory(self):
        return self.ansible_struct


if __name__ == '__main__':

    inventory = WPInventory(targets)

    print(json.dumps(inventory.get_inventory(), sort_keys=True, indent=4))
