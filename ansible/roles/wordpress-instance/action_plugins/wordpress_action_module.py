
# There is a name clash with a module in Ansible named "copy":
deepcopy = __import__('copy').deepcopy

from ansible.plugins.action import ActionBase
from ansible.errors import AnsibleError, AnsibleActionFail
from ansible.module_utils import six

import re
import os
import json

class WordPressActionModule(ActionBase):

    def run(self, tmp=None, task_vars=None):

        # We have to initialize this var to avoid any errors.
        # It will be initialized in child classes
        self.result = None

        self._tmp = tmp
        self._task_vars = task_vars

        return super(WordPressActionModule, self).run(tmp, task_vars)

    def _do_symlink_file (self, basename):
        """
        Creates a symlink for a given plugin file/folder

        :param basename: given plugin file/folder for which we have to create a symlink
        """
        return self._run_action('file', {
            'state': 'link',
            # Beware src / path inversion, as is customary with everything symlink:
            'src': self._get_symlink_target(basename),
            'path': self._get_symlink_path(basename),
            })


    def _do_rimraf_file (self, basename):
        """
        Remove a file/folder belonging to a plugin

        :param basename: given plugin file/folder
        """
        self._run_action('file',
                         {'state': 'absent',
                          'path': self._get_symlink_path(basename)})
        return self.result


    def _get_symlink_path (self, basename):
        """
        Returns symlink source path

        :param basename: given plugin file/folder for which we want the symlink source path
        """
        return self._make_element_path(self._get_wp_dir(), basename)


    def _get_symlink_target (self, basename):
        """
        Returns a path to symlink target (mu-)plugin or theme file/folder

        :param basename: given plugin file/folder for which we want the symlink target path
        """
        return self._make_element_path('../../wp', basename)


    def _make_element_path (self, prefix, basename):
        """
        Generates an absolute (mu-)plugin or theme path.

        :param prefix: string to add at the beginning of the path to have an absolute one
        :param basename: given plugin file/folder for which we want the symlink source path
        """
        return '{}/wp-content/{}s/{}'.format(prefix, self._get_type(), basename)


    def _run_wp_cli_action (self, args, update_result=True, also_in_check_mode=False, pipe_input=None, skip_loading_wp=False):
        """
        Executes a given WP-CLI command

        :param args: WP-CLI command to execute
        :param update_result: To tell if we have to update result after command. Give "False" if it is a "read only" command
        :param skip-loading-wp: if you don't want to load all the WP
        """
        # wp_cli_command: "wp --path={{ wp_dir }}"
        wp_cli_var_name = 'wp_cli_command_with_skip' if skip_loading_wp else 'wp_cli_command'
        cmd = '{} {}'.format(self._get_ansible_var(wp_cli_var_name), args)

        return self._run_shell_action(
            cmd, update_result=update_result,
            also_in_check_mode=also_in_check_mode,
            pipe_input=pipe_input)

    def _get_wp_json (self, suffix, skip_loading_wp=False):
        result = self._run_wp_cli_action(suffix, update_result=False, also_in_check_mode=True, skip_loading_wp=skip_loading_wp)
        return json.loads(result['stdout'])


    def _run_php_code(self, code, update_result=True):
        """
        Execute PHP code and returns result

        :param code: Code to execute
        :param update_result: To tell if we have to update result after command. Give "False" if it is a "read only" command
        """
        result = self._run_shell_action("php -r '{}'".format(code), update_result=update_result)

        return result['stdout_lines']


    def _run_shell_action (self, cmd, update_result=True, also_in_check_mode=False, pipe_input=None):
        """
        Executes a Shell command

        :param cmd: Command to execute.
        :param update_result: To tell if we have to update result after command. Give "False" if it is a "read only" command
        """
        return self._run_action('command', { '_raw_params': cmd, '_uses_shell': True, 'stdin': pipe_input }, update_result=update_result,
                                also_in_check_mode=also_in_check_mode)


    def _run_action (self, action_name, args, update_result=True, also_in_check_mode=False):
        """
        Executes an action, using an Ansible module.

        :param action_name: Ansible module name to use
        :param args: dict with arguments to give to module
        :param update_result: To tell if we have to update result after command. Give "False" if it is a "read only" command
        """

        self._display.vvv('_run_action(%s, %s, update_result=%s, also_in_check_mode=%s)' %
                          (action_name, args, update_result, also_in_check_mode))

        result = None
        check_mode_orig = self._play_context.check_mode
        if self._is_check_mode():
            if also_in_check_mode:
                # Get Ansible to run the task regardless
                args = deepcopy(args)
                if action_name == 'command':
                    self._play_context.check_mode = False  # Meaning that yes, it supports check mode
            else:
                # Simulate "orange" condition
                result = dict(changed=True)

        if result is None:
            try:
                result = self._do_run_action(action_name, args)
            finally:
                self._play_context.check_mode = check_mode_orig

        if update_result:
            self._update_result(result)
            return self.result

        else:
            return result


    def _do_run_action(self, action_name, args):
        try:
            # https://www.ansible.com/blog/how-to-extend-ansible-through-plugins at "Action Plugins"
            return self._execute_module(module_name=action_name,
                                        module_args=args, tmp=self._tmp,
                                        task_vars=self._task_vars)
        except AnsibleError as e:
            if not e.message.endswith('was not found in configured module paths'):
                raise e

        # Maybe action_name designates a "user-defined" action module
        # Retry through self._shared_loader_obj
        new_task = self._task.copy()
        new_task.args = args

        action = self._shared_loader_obj.action_loader.get(
            action_name,
            task=new_task,
            connection=self._connection,
            play_context=self._play_context,
            loader=self._loader,
            templar=self._templar,
            shared_loader_obj=self._shared_loader_obj)
        return action.run(task_vars=self._task_vars)


    def _get_wp_dir (self):
        """
        Returns directory in which WordPress is installed
        """
        return self._get_ansible_var('wp_dir')


    def _get_ansible_var (self, name):
        """
        Returns Ansible var value

        :param name: Var name
        """
        unexpanded = self._task_vars.get(name, None)
        if unexpanded is None:
            return None
        else:
            return self._templar.template(unexpanded)


    def _is_filename (self, from_piece):
        """
        Tells if a path is a filename/folder name or not.

        :param from_piece: string describing plugin source.
        """
        return (from_piece != "wordpress.org/plugins"
                # check if match a github repo
                and not re.match(r'^https:\/\/github\.com\/[\w-]+\/[\w-]+(\/)?$', from_piece)
                and not from_piece.endswith(".zip"))


    def _is_check_mode (self):
        return self._task_vars.get('ansible_check_mode', False)


    def _update_result (self, result):
        """
        Updates result dict

        :param result: dict to update with
        """
        oldresult = deepcopy(self.result)
        self.result.update(result)

        def _keep_flag_truthy(flag_name):
            if (flag_name in oldresult and
                oldresult[flag_name] and
                flag_name in self.result and
                not self.result[flag_name]
            ):
                self.result[flag_name] = oldresult[flag_name]

        _keep_flag_truthy('changed')

        return self.result


class WordPressPluginOrThemeActionModule(WordPressActionModule):
    """Common superclass for the wordpress_plugin and wordpress_theme action modules."""
    # Has to be set in child classes with one of the following value:
    # plugin
    # mu-plugin
    # theme
    _type = None
    # Has to be set with element name in child class
    _name = None
    # Tells if the element has to be here without any negociation (like mu-plugins) or not
    _mandatory = None


    def _get_type(self):
        """
        Return element type or raise an exception if not initialized
        """
        if self._type is None:
            raise ValueError("Please initiliaze 'self._type' in subclass {}".format(type(self).__name__))

        return self._type

    def _get_name(self):
        """
        Return element name or raise an exception if not initialized
        """
        if self._name is None:
            raise ValueError("Please initiliaze 'self._name' in children class {}".format(type(self).__name__))

        return self._name


    def _is_mandatory(self):
        """
        Return if element is mandatory or raise an exception if not initialized
        """
        if self._mandatory is None:
            raise ValueError("Please initiliaze 'self._mandatory' in children class {}".format(type(self).__name__))

        return self._mandatory


    def _get_desired_state(self):
        """
        Returns array with installation state and activation state for a (mu-)plugin or a theme.
        We look into YAML given args (plugins.yml)
        """
        desired_state = self._task.args.get('state', 'absent')
        if isinstance(desired_state, six.string_types):
             desired_state = set([desired_state.strip()])
        elif isinstance(desired_state, list):
            desired_state = set(desired_state)
        else:
            raise TypeError("Unexpected value for `state`: {}".format(desired_state))

        if 'symlinked' in desired_state and 'installed' in desired_state:
            raise ValueError('{} {} cannot be both `symlinked` and `installed`'.format(self._get_type(), self._get_name()))

        installation_state = self._installation_state(desired_state)
        activation_state = self._activation_state(desired_state)

        if installation_state == 'absent' and activation_state == 'active' and not self._is_mandatory():
            raise ValueError('{} {} cannot be simultaneously absent and {}'.format(
                             self._get_type(), self._get_name(), activation_state))

        if activation_state == 'active' or self._is_mandatory():
            # Cannot activate (or make a mu-plugin) if not installed
            if not installation_state:
                installation_state = 'symlinked'
        if installation_state == 'absent':
            # Must (attempt to) deactivate prior to uninstalling
            if not activation_state:
                activation_state = "inactive"

        return (installation_state, activation_state)


    def _ensure_file_state (self, desired_state, basename):
        """
        Check if a given (mu-)plugin file/folder is at the desired state

        :param desired_state: can be 'installed', 'symlinked', ...
        :param basename: name of element to check (can be a file or folder)
        """
        current_state = set([self._get_current_file_state(basename)])
        to_do = set([desired_state]) - current_state
        to_undo = current_state - set([desired_state])

        if not (to_do or to_undo):
            return

        if 'installed' in to_do:
            self._update_result(self._run_wp_cli_action('plugin install {}'.format(self._task.args.get('from'))))

        if 'symlinked' in to_undo or 'installed' in to_undo:
            self._update_result(self._do_rimraf_file(basename))
            if 'failed' in self.result: return self.result

        if 'symlinked' in to_do:
            self._update_result(self._do_symlink_file(basename))
            if 'failed' in self.result: return self.result


    def _ensure_all_files_state (self, desired_state):
        """
        Checks if all files/folder for a plugin are in the desired states (present, absent, ...)

        :param desired_state: can be 'installed', 'symlinked', ...
        """
        froms = self._task.args.get('from')
        if isinstance(froms, six.string_types):
            froms = [froms]
        if not froms:
            froms = []

        basenames = [os.path.basename(f) for f in froms
                if self._is_filename(f)]
        if not basenames:
            basenames = [self._get_name()]

        # Going through each files/folder for plugin
        for basename in basenames:
            self._ensure_file_state(desired_state, basename)
            if 'failed' in self.result: return self.result


    def _get_current_file_state (self, basename):
        """
        Returns state of a given plugin file/folder.

        :param basename: name of element to check (can be a file or folder)
        """
        path = self._get_symlink_path(basename)
        plugin_stat = self._run_action('stat', { 'path': path }, update_result=False, also_in_check_mode=True)
        if 'failed' in plugin_stat:
            raise AnsibleActionFail("Cannot stat() {} - Error: {}".format(path, plugin_stat))
        file_exists = ('stat' in plugin_stat and plugin_stat['stat']['exists'])
        if not file_exists:
            return 'absent'
        if not plugin_stat['stat']:
            return 'absent'
        elif plugin_stat['stat']['islnk']:
            if (plugin_stat['stat']['lnk_target'] ==
                self._get_symlink_target(basename)):
                return 'symlinked'
            else:
                return 'symlink_damaged'
        else:
            return 'installed'


    def _do_activate_element(self):
        """
        Uses WP-CLI to activate plugin
        """
        return self._run_wp_cli_action('{} activate {}'.format(self._get_type(), self._get_name()))


    def _activation_state(self, desired_state):
        """
        Returns plugin activation state based on desired state (active, inactive)

        :param desired_state: Plugin desired activation state
        """

        # Active by default
        if self._is_mandatory():
            return 'active'

        activation_state = desired_state.intersection(['active', 'inactive'])
        if len(activation_state) == 0:
            return None
        elif len(activation_state) == 1:
            return list(activation_state)[0]
        else:
            raise ValueError('{} {} cannot be simultaneously {}'.format(self._get_type(), self._get_name(), str(list(activation_state))))


    def _installation_state(self, desired_state):
        """
        Returns plugin installation state based on desired state (present, absent, symlinked)

        :param desired_state: Plugin desired installation state
        """
        installation_state = desired_state.intersection(['present', 'absent', 'symlinked', 'installed'])
        if len(installation_state) == 0:
            return None
        elif len(installation_state) == 1:
            return list(installation_state)[0]
        else:
            raise ValueError('{} {} cannot be simultaneously {}'.format(self._get_type(), self._get_name(), str(list(installation_state))))


    def _get_activation_state (self):
        """
        Returns plugin activation state
        """
        # To use 'wp plugin' for MU-Plugins
        wp_command = 'plugin' if self._get_type() == 'mu-plugin' else self._get_type()

        result = self._run_wp_cli_action('{} list --format=csv'.format(wp_command), also_in_check_mode=True, update_result=False)

        if 'failed' in result: return

        for line in result["stdout"].splitlines()[1:]:
            fields = line.split(',')
            if len(fields) < 2: continue
            if fields[0] == self._get_name(): return fields[1]
        return 'inactive'
