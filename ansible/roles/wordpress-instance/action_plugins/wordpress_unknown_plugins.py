"""What to do with unknown WordPress plug-ins.

Right now the only supported action is to delete them (with "state: absent").
"""

import sys
import os.path
import yaml

from ansible.plugins.action import ActionBase

sys.path.append(os.path.dirname(__file__))
from wordpress_action_module import WordPressActionModule
from wordpress_plugin import ActionModule as WordPressPluginActionModule

class ActionModule(WordPressActionModule):
    def run(self, tmp=None, task_vars=None):
        self.result = super(ActionModule, self).run(tmp, task_vars)

        state = self._task.args.get('state')
        if not state:
            return
        elif state != 'absent':
            raise AnsibleActionFail("Unknown state '%s' for wordpress_unknown_plugins" % state)

        if 'wordpress_unknown_plugins' not in self.result:
            self.result['wordpress_unknown_plugins'] = []
        for name in self.get_installed_or_symlinked_plugins(task_vars):
            if name not in self.known_plugins:
                self._run_action('wordpress_plugin', dict(name=name, state=state))
                self.result['wordpress_unknown_plugins'].append(name)

        return self.result

    def get_installed_or_symlinked_plugins(self, task_vars):
        unexpanded = task_vars.get('wp_plugin_list', None)
        if unexpanded is None:
            return set()

        wp_plugin_list = self._templar.template(unexpanded)
        return set(p['name'] for p in wp_plugin_list if p['status'] != 'must-use')

    @property
    def known_plugins(self):
        if not hasattr(self, '_known_plugins'):
            self._known_plugins = set(self._scrape_known_plugins(self._task.args['known_plugins_in']))
        return self._known_plugins


    def _scrape_known_plugins(self, path):
        parsed = yaml.safe_load(open(path))
        for task in parsed:
            task_args = task.get('wordpress_plugin')
            if type(task_args) is not dict:
                continue
            if 'name' in task_args:
                yield task_args['name']
