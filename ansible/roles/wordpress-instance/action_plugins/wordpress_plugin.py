# -*- coding: utf-8 -*-

# There is a name clash with a module in Ansible named "copy":
deepcopy = __import__('copy').deepcopy
import re
import sys
import os.path
import json

# To be able to include package wp_inventory in parent directory
sys.path.append(os.path.dirname(__file__))

from ansible.errors import AnsibleActionFail
from ansible.module_utils import six
from wordpress_action_module import WordPressActionModule

class ActionModule(WordPressActionModule):
    def run (self, tmp=None, task_vars=None):

        self.result = super(ActionModule, self).run(tmp, task_vars)
        
        self._plugin_name = self._task.args.get('name')
        self._is_mu = self._task.args.get('is_mu', False)

        current_activation_state = self._get_plugin_activation_state()
        (desired_installation_state,
         desired_activation_state) = self._get_desired_state()

        if (
                bool(desired_activation_state) and
                'active' in set([current_activation_state]) - set([desired_activation_state])
        ):
            self._update_result(self._do_deactivate_plugin())
            if 'failed' in self.result: return self.result

        if desired_installation_state:
            # We don't second-guess mu-plugins - If the activation
            # state is left vague, then they will be "demoted" to
            # ordinary plug-ins.
            self._ensure_all_files_state(desired_installation_state, self._is_mu)
            if 'failed' in self.result: return self.result
            self._ensure_all_files_state('absent', not self._is_mu)
            if 'failed' in self.result: return self.result

        if (
                not self._is_mu and
                bool(desired_activation_state) and
                'active' in set([desired_activation_state]) - set([current_activation_state])
        ):
            
            
            self._update_result(self._do_activate_plugin())
            if 'failed' in self.result: return self.result

        return self.result

    def _ensure_all_files_state (self, desired_state, is_mu):
        """
        Checks if all files/folder for a plugin are in the desired states (present, absent, ...)

        :param desired_state: can be 'installed', 'symlinked', ...
        :param is_mu: Boolean to tell if plugin is a MU-Plugin
        """

        froms = self._task.args.get('from')
        if isinstance(froms, six.string_types):
            froms = [froms]
        if not froms:
            froms = []
        
        basenames = [os.path.basename(f) for f in froms
                if self._is_filename(f)]
        if not basenames:
            basenames = [self._plugin_name]

        # Going through each files/folder for plugin
        for basename in basenames:
            self._ensure_file_state(desired_state, basename, is_mu)
            if 'failed' in self.result: return self.result



    def _ensure_file_state (self, desired_state, basename, is_mu):
        """
        Check if a given (mu-)plugin file/folder is at the desired state

        :param desired_state: can be 'installed', 'symlinked', ...
        :param basename: name of element to check (can be a file or folder)
        :param is_mu: Boolean to tell if it's a Mu-Plugin
        """
        current_state = set([self._get_current_file_state(basename, is_mu)])
        to_do = set([desired_state]) - current_state
        to_undo = current_state - set([desired_state])

        if not (to_do or to_undo):
            return

        if 'installed' in to_do:
            raise NotImplementedError('Installing "regular" (non-symlinked) plugin %s '
                                      'not supported (yet)' % basename)

        if 'symlinked' in to_undo or 'installed' in to_undo:
            self._update_result(self._do_rimraf_file(basename, is_mu))
            if 'failed' in self.result: return self.result

        if 'symlinked' in to_do:
            self._update_result(self._do_symlink_file(basename, is_mu))
            if 'failed' in self.result: return self.result


    def _get_current_file_state (self, basename, is_mu):
        """
        Returns state of a given plugin file/folder.

        :param basename: name of element to check (can be a file or folder)
        :param is_mu: Boolean to tell if it's a Mu-Plugin
        """
        path = self._get_symlink_path(basename, is_mu)
        plugin_stat = self._run_action('stat', { 'path': path })
        if 'failed' in plugin_stat:
            raise AnsibleActionFail("Cannot stat() %s" % path)
        file_exists = ('stat' in plugin_stat and plugin_stat['stat']['exists'])
        if not file_exists:
                return 'absent'
        elif plugin_stat['stat']['islnk']:
            if (plugin_stat['stat']['lnk_target'] ==
                self._get_symlink_target(basename, is_mu)):
                return 'symlinked'
            else:
                return 'symlink_damaged'
        else:
            return 'installed'


    def _get_desired_state(self):
        """
        Returns array with installation state and activation state for a (mu-)plugin.
        We look into YAML given args (plugins.yml)
        """
        desired_state = self._task.args.get('state', 'absent')
        if isinstance(desired_state, six.string_types):
             desired_state = set([desired_state.strip()])
        elif isinstance(desired_state, list):
            desired_state = set(desired_state)
        else:
            raise TypeError("Unexpected value for `state`: %s" % desired_state)

        if 'symlinked' in desired_state and 'installed' in desired_state:
            raise ValueError('Plug-in %s cannot be both `symlinked` and `installed`' % self._plugin_name)

        installation_state = self._installation_state(desired_state)
        activation_state = self._activation_state(desired_state)

        if installation_state == 'absent' and (activation_state == 'active' or self._is_mu):
            raise ValueError('Plug-in %s cannot be simultaneously absent and %s' %
                             self._plugin_name, activation_state)

        if activation_state == 'active' or self._is_mu:
            # Cannot activate (or make a mu-plugin) if not installed
            if not installation_state:
                installation_state = 'symlinked'
        if installation_state == 'absent':
            # Must (attempt to) deactivate prior to uninstalling
            if not activation_state:
                activation_state = "inactive"

        return (installation_state, activation_state)


    def _installation_state(self, desired_state):
        """
        Returns plugin installation state based on desired state (present, absent, symlinked)

        :param desired_state: Plugin desired installation state
        """
        installation_state = desired_state.intersection(['present', 'absent', 'symlinked'])
        if len(installation_state) == 0:
            return None
        elif len(installation_state) == 1:
            return list(installation_state)[0]
        else:
            raise ValueError('Plug-in cannot be simultaneously %s' % str(list(installation_state)))


    def _activation_state(self, desired_state):
        """
        Returns plugin activation state based on desired state (active, inactive)

        :param desired_state: Plugin desired activation state
        """

        # Active by default
        if self._is_mu:
            return 'active'

        activation_state = desired_state.intersection(['active', 'inactive'])
        if len(activation_state) == 0:
            return None
        elif len(activation_state) == 1:
            return list(activation_state)[0]
        else:
            raise ValueError('Plug-in %s cannot be simultaneously %s' % str(list(activation_state)))


    def _do_symlink_file (self, basename, is_mu):
        """
        Creates a symlink for a given plugin file/folder

        :param basename: given plugin file/folder for which we have to create a symlink
        :param is_mu: Boolean to tell if it's a mu-plugin
        """
        return self._run_action('file', {
            'state': 'link',
            # Beware src / path inversion, as is customary with everything symlink:
            'src': self._get_symlink_target(basename, is_mu),
            'path': self._get_symlink_path(basename, is_mu),
            })


    def _get_symlink_target (self, basename, is_mu):
        """
        Returns a path to symlink target plugin file/folder

        :param basename: given plugin file/folder for which we want the symlink target path
        :param is_mu: Boolean to tell if it's a mu-plugin
        """
        return self._make_plugin_path('../../wp', basename, is_mu)


    def _do_activate_plugin (self):
        """
        Uses WP-CLI to activate plugin
        """
        return self._run_wp_cli_action('plugin activate %s' % self._plugin_name)


    def _do_deactivate_plugin (self):
        """
        Uses WP-CLI to deactivate plugin
        """
        return self._run_wp_cli_action('plugin deactivate %s' % self._plugin_name)


    def _do_rimraf_file (self, basename, is_mu):
        """
        Remove a file/folder belonging to a plugin

        :param basename: given plugin file/folder
        :param is_mu: Boolean to tell if it's a mu-plugin
        """
        self._run_action('file',
                         {'state': 'absent',
                          'path': self._get_symlink_path(basename, is_mu)})
        return self.result


    def _get_symlink_path (self, basename, is_mu):
        """
        Returns symlink source path

        :param basename: given plugin file/folder for which we want the symlink source path
        :param is_mu: Boolean to tell if it's a mu-plugin
        """
        return self._make_plugin_path(self._get_wp_dir(), basename, is_mu)


    def _make_plugin_path (self, prefix, basename, is_mu):
        """
        Generates an absolute (mu-)plugin path.

        :param prefix: string to add at the beginning of the path to have an absolute one
        :param basename: given plugin file/folder for which we want the symlink source path
        :param is_mu: Boolean to tell if it's a mu-plugin
        """
        return '%s/wp-content/%splugins/%s' % (
            prefix,
            'mu-' if is_mu else '',
            basename)


    def _get_plugin_activation_state (self):
        """
        Returns plugin activation state
        """
        oldresult = deepcopy(self.result)
        result = self._run_wp_cli_action('plugin list --format=csv')
        if 'failed' in self.result: return

        self.result = oldresult  # We don't want "changed" to pollute the state

        for line in result["stdout"].splitlines()[1:]:
            fields = line.split(',')
            if len(fields) < 2: continue
            if fields[0] == self._plugin_name: return fields[1]
        return 'inactive'
