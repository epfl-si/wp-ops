"""WordPress facts, without the facts.d nonsense.

Usage in a task file or playbook:

  - wordpress_facts:

Collects all the facts from the current WordPress.

Configuration is done through Ansible variables:

`wp_dir`
: The directory to examine for the `wp_is_installed` and `wp_is_symlinked` facts
`wp_cli_command`
: The prefix for all wp-cli commands to execute, e.g. `wp --path {{ wp_dir }}`

"""

import sys
import os.path

sys.path.append(os.path.dirname(__file__))
from wordpress_action_module import WordPressActionModule


class ActionModule(WordPressActionModule):
    def run(self, tmp=None, task_vars=None):

        self.result = super(ActionModule, self).run(tmp, task_vars)

        try:
            wp_is_installed = self._is_wp_installed()
            wp_is_symlinked = self._is_wp_symlinked()
        except Exception as e:
            self.result['failed'] = True
            self.result['exception'] = repr(e)
            return self.result

        facts = {
            'wp_is_installed': wp_is_installed,
            'wp_is_symlinked': wp_is_symlinked
        }
        self.result['ansible_facts'] = { 'ansible_local': facts }

        if wp_is_installed:
            for wat in ['plugin', 'theme']:
                try:
                    facts['wp_%s_list' % wat] = self._get_wp_json('%s list --format=json' % wat, skip_loading_wp=True)
                except:
                    pass

        return self.result

    def _is_wp_installed (self):
        stat = self._stat('wp-config.php')
        return ('stat' in stat) and (stat['stat']['exists'])

    def _is_wp_symlinked (self):
        stat = self._stat('wp-admin')
        return not (('stat' in stat) and stat['stat'] and 'isdir' in stat['stat'] and (stat['stat']['isdir']))

    def _stat (self, relpath):
        return self._run_action('stat', {
            'path': os.path.join(self._get_wp_dir(), relpath)
        }, update_result=False, also_in_check_mode=True)
