# Create or delete a Polylang language and translation ("polylang-mo")

# To be able to import wordpress_action_module
import sys
import os
import json
from ansible.errors import AnsibleActionFail

sys.path.append(os.path.dirname(__file__))
from wordpress_action_module import WordPressActionModule

class ActionModule(WordPressActionModule):

    MAIN_MENU = "Main"
    FOOTER_MENU = "footer_nav"

    def run(self, tmp=None, task_vars=None):
        self.result = super(ActionModule, self).run(tmp, task_vars)

        desired_state = self._task.args.get('state', 'absent')
        if desired_state == "present":
            self.ensure_polylang_menu()

        return self.result

    # Ensure that a menu exists for each languages
    def ensure_polylang_menu(self):

        import sys;sys.path.append("/home/greg/.local/share/JetBrains/IntelliJIdea2020.1/python/helpers/pydev/");import pydevd_pycharm; pydevd_pycharm.settrace('localhost', port=12345, stdoutToServer=True, stderrToServer=True)

        theme_name = self._run_wp_cli_action("theme list --status=active --field=name", update_result=False)['stdout']

        polylang_options = self._get_wp_json("option get polylang --format=json")

        if 'nav_menus' in polylang_options and theme_name in polylang_options['nav_menus'] and "top" in polylang_options['nav_menus'][theme_name]:

            actual_languages = [lang['slug'] for lang in self._get_wp_json("pll lang list --format=json")]
            for actual_lang in actual_languages:
                if actual_lang in polylang_options['nav_menus']['epfl_master']['top']:
                    pass
                else:
                    # create menu for actual lang
                    pass
        else:
            # TODO: Create all TOP menus
            # create menus if they don't exist
            self.run_wp_cli("pll menu create {} top".format(self.MAIN_MENU))

            # TODO: Create this line after daily discussion ?
            # self.run_wp_cli("pll menu create {} footer_nav".format(settings.FOOTER_MENU))



