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
        
        self._name = self._task.args.get('name')
        self._mandatory = self._task.args.get('is_mu', False)
        self._type = 'mu-plugin' if self._task.args.get('is_mu', False) else 'plugin'

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
            # Setting desired installation state
            self._ensure_all_files_state(desired_installation_state)
            if 'failed' in self.result: return self.result

        if (
                not self._is_mandatory() and
                bool(desired_activation_state) and
                'active' in set([desired_activation_state]) - set([current_activation_state])
        ):
            
            
            self._update_result(self._do_activate_plugin())
            if 'failed' in self.result: return self.result

        return self.result


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
            raise NotImplementedError('Installing "regular" (non-symlinked) plugin %s '
                                      'not supported (yet)' % basename)

        if 'symlinked' in to_undo or 'installed' in to_undo:
            self._update_result(self._do_rimraf_file(basename))
            if 'failed' in self.result: return self.result

        if 'symlinked' in to_do:
            self._update_result(self._do_symlink_file(basename))
            if 'failed' in self.result: return self.result


    def _get_current_file_state (self, basename):
        """
        Returns state of a given plugin file/folder.

        :param basename: name of element to check (can be a file or folder)
        """
        path = self._get_symlink_path(basename)
        plugin_stat = self._run_action('stat', { 'path': path })
        if 'failed' in plugin_stat:
            raise AnsibleActionFail("Cannot stat() %s" % path)
        file_exists = ('stat' in plugin_stat and plugin_stat['stat']['exists'])
        if not file_exists:
                return 'absent'
        elif plugin_stat['stat']['islnk']:
            if (plugin_stat['stat']['lnk_target'] ==
                self._get_symlink_target(basename)):
                return 'symlinked'
            else:
                return 'symlink_damaged'
        else:
            return 'installed'



    def _do_activate_plugin (self):
        """
        Uses WP-CLI to activate plugin
        """
        return self._run_wp_cli_action('plugin activate %s' % self._get_name())


    def _do_deactivate_plugin (self):
        """
        Uses WP-CLI to deactivate plugin
        """
        return self._run_wp_cli_action('plugin deactivate %s' % self._get_name())


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
            if fields[0] == self._get_name(): return fields[1]
        return 'inactive'
