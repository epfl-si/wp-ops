
import subprocess
import shlex
import re
import json

class WPInventory():

    def __init__(self, targets, prune_elements, env_prefix):
        """
        Class constructor

        :param targets: Dict with options to connect to env on which doing inventory.
                        Contains following keys: ssh_port, ssh_user, ssh_host, remote_path
        :param prune_elements: Dict with elements to prune while using 'find' command.
                                Can have 'name' and 'path' keys with a list of element to prune
        :param env_prefix: Prefix to use for environement (prod, test, dev)
        """
        self._nicknames_already_taken = []
        self._wordpresses = {}
        self._env_prefix = env_prefix

        for target in targets:
            for wordpress_instance in self._collect_wordpress_installs_over_ssh(target, prune_elements):
                wordpress_instance = {**target, **wordpress_instance}
                category = self._categorize(wordpress_instance)
                
                if category not in self._wordpresses:
                    self._wordpresses[category] = []
                
                self._wordpresses[category].append(wordpress_instance)

        self._as_ansible_struct()


    def _categorize(self, wp):
        """
        Determines which Ansible group a given Wordpress goes into

        :param wp: Dict with WP information
        """
        wp_env = wp['wp_env']

        if wp_env == 'form':
            cat_nickname = 'formation'
        elif wp_env.startswith('unm-'):
            cat_nickname = 'unmanaged'
        else:
            cat_nickname = wp_env

        return "{}-{}".format(self._env_prefix, cat_nickname)


    def _exec_ssh(self, target_dict, cmd):
        """
        Executes a SSH command using information contained in target_dict dictionnary.
        Returns result.


        """
        
        ssh_cmd = 'ssh -xT -q -p {} -o StrictHostKeyChecking=no {}@{} "{}"'.format(target_dict['ssh_port'],
                                                                        target_dict['ssh_user'],
                                                                        target_dict['ssh_host'],
                                                                        cmd)
        args = shlex.split(ssh_cmd)
        ssh =  subprocess.Popen(args, 
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                shell=False)

        result = ssh.stdout.readlines()

        if result == []:
            error = ssh.stderr.readlines()
            raise ValueError("ERROR: {}".format(error))
    
        return result


    def _collect_wordpress_installs_over_ssh(self, target_dict, prune_elements):
        """
        Use SSH to get all installed WordPress website information.

        :param target_dict: dict containing information about target to connect to get WP instances information.
        :param prune_elements: Dict with elements to prune while using 'find' command.
                                Can have 'name' and 'path' keys with a list of element to prune
        """

        # We assume we always have 'name' key inside prune_elements dict

        prune_options = '-name {}'.format(' -o -name '.join(prune_elements['name']))

        # Adding path prune option if given
        if 'path' in prune_elements:
            prune_options = '{} -o -path {}'.format(prune_options, ' -o -path '.join(prune_elements['path']))

        cmd_to_exec = "find {} \( -type d \( {} \) -prune -false -o -name wp-config.php \)".format(target_dict['remote_path'], prune_options)

        result = self._exec_ssh(target_dict, cmd_to_exec)
        
        retval = []

        for line in result:
            line = line.decode().strip()
            values = re.findall(r'/srv/([^/]*)/([^/]*)/htdocs/(.*?)/?wp-config.php$', line)

            if values:
                # Recovering instance details
                details = self._instance_details(target_dict, line.replace('wp-config.php', ''))

                retval.append({'wp_env': values[0][0],
                                'wp_hostname': values[0][1],
                                'wp_path': values[0][2],
                                'wp_details': details})
            else:
                raise ValueError("Bizarre in line {}".format(line))

        return retval


    def _instance_details(self, target_dict, path_to_instance):
        """
        Gathers more information about a WordPress install and return a dict 

        :param target_dict: dict containing information about target to connect to get WP instances information.
        :param path_to_instance: Path to access instance
        """
        details = {}


        ## 1. Options
        section = 'options'
        details[section] = {}
        # List of options to get from Instance
        options_to_get = ['plugin:epfl_accred:unit_id', 
                          'plugin:epfl_accred:unit',
                          'epfl:site_category',
                          'siteurl']

        # Default value for options
        for option_name in options_to_get:
            details[section][option_name] = None

        try:
            instance_options = self._exec_ssh(target_dict, 'wp option list --path={} --format=csv --skip-themes --skip-plugins'.format(path_to_instance))

            # Looping through instance options to find the ones we want
            for instance_option in instance_options:

                # Extracting information
                values = re.findall(r'^([\w:_-]+),\"?(.+)\"?$', instance_option.decode().strip())

                if values and values[0][0] in options_to_get:
                    # We save option and remove potential " around the string.
                    details[section][values[0][0]] = (values[0][1]).strip('"')

        except Exception as e:
            details[section]['_error'] = 'Error getting options: {}'.format(e)

        
        ## 2. Defined boolean
        section = 'debug'
        details[section] = {}

        defined_to_check = ['WP_DEBUG', 'WP_DEBUG_DISPLAY', 'WP_DEBUG_LOG']
        for defined in defined_to_check:
            try:
                result = self._exec_ssh(target_dict, "wp config get {} --path={} --skip-themes --skip-plugins".format(defined, path_to_instance))

                # To handle result, we have to decode it because it comes in 'byte' mode.
                details[section][defined] = result[0].decode().strip('\n')=="1"

            # If exception, it means we can't get the value because it's not present in config file
            except Exception as e:
                details[section][defined] = False
        
        # Check debug log file size
        try:
            
            result = self._exec_ssh(target_dict, "if [ -e '{0}/wp-content/debug.log' ] ;then stat --printf='%s' '{0}/wp-content/debug.log' ;else echo '0'; fi".format(path_to_instance))
            details[section]['log_file_size'] = int(result[0].decode().strip('\n'))

        except Exception as e:
            details[section]['log_file_size'] = 0
            details[section]['_error'] = 'Error getting log file infos: {}'.format(e)


        return details


    def _as_ansible_struct(self):
        """
        Transforms WP list to a structure that can be used by Ansible.
        """
        # https://docs.ansible.com/ansible/latest/dev_guide/developing_inventory.html

        self._ansible_struct = {'all-wordpresses': { 'children': [ '{}-wordpresses'.format(self._env_prefix) ] },
                                '_meta': { 'hostvars': {} } }

        for category  in self._wordpresses:
            for wp in self._wordpresses[category]:

                wp = self._as_ansible_hostvars(wp)

                nickname = self._nickname(wp)

                if category not in self._ansible_struct:
                    self._ansible_struct[category] = {'hosts': []}
                
                self._ansible_struct[category]['hosts'].append(nickname)

                self._ansible_struct['_meta']['hostvars'][nickname] = wp
        
        # Adding all categories as children
        self._ansible_struct['{}-wordpresses'.format(self._env_prefix)] = { 'children': list(self._wordpresses.keys())}

    
    def _as_ansible_hostvars(self, wp):
        """
        Transforms a WP instance (dict) to a dict that can be used by Ansible

        :param wp: Dict with WP information
        """
        
        retval = {
            'ansible_python_interpreter': '/usr/bin/python3',
            'openshift_namespace': 'wwp-{}'.format(self._env_prefix),
            'wp_ensure_symlink_version': '5.2'
        }
        
        for key, val in wp.items():
            if re.match(r'^(ssh|wp|ansible)_', key):
                key = re.sub(r'^ssh_', 'ansible_', key)
                retval[key] = val if val is not None else ''

        return retval


    def _nickname(self, wp):
        """
        Generates an unique nickname for a WP instance.

        :param wp: Dict with WP information
        """
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
        while nickname in self._nicknames_already_taken:
            uniq += 1
            nickname = "{}{}".format(steam, uniq)
        
        self._nicknames_already_taken.append(nickname)

        return nickname


    def get_inventory(self):
        """
        Returns dict that can be used by Ansible
        """
        return self._ansible_struct
