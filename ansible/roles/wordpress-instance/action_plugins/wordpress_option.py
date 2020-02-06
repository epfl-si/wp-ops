import sys
import os.path

# To be able to include package wp_inventory in parent directory
sys.path.append(os.path.dirname(__file__))

from ansible.plugins.action import ActionBase
from wordpress_action_module import WordPressActionModule


class ActionModule(WordPressActionModule):
    def run(self, tmp=None, task_vars=None):
        
        self.result = super(ActionModule, self).run(tmp, task_vars)

        self._update_result(self._update_option())

        return self.result


    def _update_option(self):
        """
        Update and existing option or add it if not exists
        """

        return self._run_wp_cli_action('option update {} "{}"'.format(self._task.args.get('option_name'), 
                                                                      self._task.args.get('option_value')))

    
