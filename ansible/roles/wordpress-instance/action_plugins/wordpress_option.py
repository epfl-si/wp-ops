import sys
import os.path
import re

# To be able to import wordpress_action_module
sys.path.append(os.path.dirname(__file__))

from wordpress_action_module import WordPressActionModule


class ActionModule(WordPressActionModule):
    def run(self, tmp=None, task_vars=None):

        self.result = super(ActionModule, self).run(tmp, task_vars)

        # Handling --check execution mode
        if task_vars['ansible_check_mode']:
            self.result['skipped'] = True
            return self.result

        self._update_option()

        return self.result


    def _update_option(self):
        """
        Update and existing option or add it if not exists

        NOTE: Apart 'name' and 'value', we could also have an 'autoload' value but after some tests,
        WP-CLI, even if documented to use '--autoload' parameter, raises an error...
        """

        option_value = str(self._task.args.get('value')).strip()

        json_format = ''

        # If option is serialized
        if re.match(r'^a:\d+:\{.*\}', option_value):

            # Escaping double quotes to avoid problems and unserializing option value and converting it to JSON to reuse it
            # We use PHP do to this because Python doesn't have the appropriate functions for this.. not his job !
            php_cmd = 'echo json_encode(unserialize("{0}"));'.format(option_value.replace('"', '\\"'))
            option_value = self._run_php_code(php_cmd, update_result=False)

            option_value = option_value[0] if len(option_value) > 0 else ''

            # If we have a value, it is JSON
            if option_value != '':
                json_format = '--format=json'

        changed_status_orig = self.result.get('changed')
        cmd = "option update {} {} '{}' --skip-themes --skip-plugins".format(json_format, self._task.args.get('name'), option_value)
        result = self._run_wp_cli_action(cmd)
        if result.get('failed'):
            return

        if 'option is unchanged.' in result['stdout']:
            if changed_status_orig is not None:
                self.result['changed'] = changed_status_orig
            else:
                del self.result['changed']
