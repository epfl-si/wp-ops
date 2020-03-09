import sys
import os.path
import re

# To be able to include package wp_inventory in parent directory
sys.path.append(os.path.dirname(__file__))

from wordpress_action_module import WordPressActionModule


class ActionModule(WordPressActionModule):
    def run(self, tmp=None, task_vars=None):
        
        self.result = super(ActionModule, self).run(tmp, task_vars)

        # Getting command to execute
        wpcli_command = str(self._task.args.get('wpcli_command')).strip()

        if wpcli_command != "":

            # Executing command and updating result
            self._update_result(self._run_wp_cli_action(wpcli_command))

        return self.result
