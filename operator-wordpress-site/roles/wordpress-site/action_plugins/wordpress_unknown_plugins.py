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
from ansible.errors import AnsibleError

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
        for plugin in self.get_installed_or_symlinked_plugins_and_muplugins(task_vars):
            name = plugin['name']
            if name not in self.known_plugins:
                task_args = dict(name=name, state=state)
                task_args['is_mu'] = plugin.get('status') == 'must-use'
                self._subaction.change(
                    'wordpress_plugin', task_args, update_result=self.result)
                self.result['wordpress_unknown_plugins'].append(dict(
                    name=name,
                    is_mu=task_args['is_mu']))

        return self.result

    def get_installed_or_symlinked_plugins_and_muplugins(self, task_vars):
        unexpanded = task_vars.get('wp_plugin_list', None)
        if unexpanded is None:
            return set()
        else:
            return self._templar.template(unexpanded)

    @property
    def known_plugins(self):
        if not hasattr(self, '_known_plugins'):
            self._known_plugins = set(self._scrape_known_plugins(self._task.args['known_plugins_in']))
            if not self._known_plugins:
                raise AnsibleError("No known plugins?! Refusing to proceed.")
        return self._known_plugins


    def _scrape_known_plugins(self, path):
        parsed = yaml.safe_load(open(path))
        for task in parsed:
            task_args = task.get('wordpress_plugin')
            if type(task_args) is not dict:
                continue
            if 'name' in task_args:
                yield task_args['name']
