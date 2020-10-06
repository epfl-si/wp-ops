
# There is a name clash with a module in Ansible named "copy":
deepcopy = __import__('copy').deepcopy

import sys
import os.path

# To be able to import wordpress_action_module
sys.path.append(os.path.dirname(__file__))

from wordpress_action_module import WordPressPluginOrThemeActionModule

class ActionModule(WordPressPluginOrThemeActionModule):
    def run(self, tmp=None, task_vars=None):
        self.result = super(ActionModule, self).run(tmp, task_vars)

        self._name = self._task.args.get('name')
        self._type = 'theme'
        self._mandatory = False

        current_activation_state = self._get_activation_state()
        (desired_installation_state,
         desired_activation_state) = self._get_desired_state()

        if desired_installation_state:
            # Setting desired installation state
            self._ensure_all_files_state(desired_installation_state)

        if (
                bool(desired_activation_state) and
                'active' in set([desired_activation_state]) - set([current_activation_state])
        ):
            
            
            self._do_activate_element()

        return self.result
