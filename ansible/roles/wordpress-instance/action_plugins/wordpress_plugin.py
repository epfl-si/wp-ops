# -*- coding: utf-8 -*-

# There is a name clash with a module in Ansible named "copy":
deepcopy = __import__('copy').deepcopy
import re
import sys
import os.path
import json

# The next two `import`s are from the same directory as this module:
thisdir = os.path.dirname(__file__)
if thisdir not in sys.path:
    sys.path.append(thisdir)

from cache import InMemoryDecoratorCache, OnDiskDecoratorCache
from wordpress_action_module import WordPressPluginOrThemeActionModule

on_disk_cache_path = os.getenv("WPSIBLE_WPCLI_CACHE_DIR")
if on_disk_cache_path is not None:
    query_cache = OnDiskDecoratorCache(on_disk_cache_path)
else:
    query_cache = InMemoryDecoratorCache()

class ActionModule(WordPressPluginOrThemeActionModule):
    def run (self, tmp=None, task_vars=None):

        self.result = super(ActionModule, self).run(tmp, task_vars)

        self._name = self._task.args.get('name')
        self._mandatory = self._task.args.get('is_mu', False)
        self._type = 'mu-plugin' if self._task.args.get('is_mu', False) else 'plugin'

        current_activation_state = self._get_activation_state()
        (desired_installation_state,
         desired_activation_state) = self._get_desired_state()

        if (
                bool(desired_activation_state) and
                'active' in set([current_activation_state]) - set([desired_activation_state])
        ):
            self._do_deactivate_plugin()

        if desired_installation_state:
            # Setting desired installation state
            self._ensure_all_files_state(desired_installation_state)

        if (
                not self._is_mandatory() and
                bool(desired_activation_state) and
                'active' in set([desired_activation_state]) - set([current_activation_state])
        ):
            self._do_activate_element()

        return self.result

    def _ensure_all_files_state (self, desired_state):
        """Overridden to try with `wp plugin delete` first."""
        # First try to use wp-cli to uninstall:
        if desired_state == 'absent' and not self._is_check_mode():
            orig_changed = self.result.get('changed', False)
            self._run_wp_cli_change('plugin delete {}'.format(self._task.args.get('name')))
            if ("Plugin already deleted" in self.result["stdout"]
                or "could not be found" in self.result["stdout"]):
                self.result['changed'] = orig_changed

        super(ActionModule, self)._ensure_all_files_state(desired_state)


    def _do_deactivate_plugin (self):
        """
        Uses WP-CLI to deactivate plugin
        """
        return self._run_wp_cli_change('plugin deactivate {}'.format(self._get_name()))

    @query_cache.by(lambda self, args: (self._inventory_hostname, args))
    def _query_wp_cli (self, args):
        """Overridden for caching."""
        return super(ActionModule, self)._query_wp_cli(args)

    @query_cache.invalidate_by_prefix(lambda self: (self._inventory_hostname, ))
    def _run_wp_cli_change(self, args, pipe_input=None):
        """Overridden for caching."""
        return super(ActionModule, self)._run_wp_cli_change(args, pipe_input=pipe_input)
