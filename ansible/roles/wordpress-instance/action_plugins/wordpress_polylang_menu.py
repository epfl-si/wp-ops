# Ensure that a menu exists in the "Top" location for every language.
# Note that the name of the menu *does not* matter, as some sites (e.g. www.epfl.ch/schools/ic)
# already use one or more renamed menus in the "Top" location.

import sys
import os
import json
from ansible.errors import AnsibleActionFail

# To be able to import wordpress_action_module
sys.path.append(os.path.dirname(__file__))
from wordpress_action_module import WordPressActionModule

class ActionModule(WordPressActionModule):

    MAIN_MENU = "Main"

    def run(self, tmp=None, task_vars=None):
        self.result = super(ActionModule, self).run(tmp, task_vars)
        desired_state = self._task.args.get('state', 'absent')
        if desired_state == "present":
            self.ensure_polylang_main_menu()
        return self.result

    def _menu_exists(self, menu_name):
        """
        Tells if a menu exists

        Keyword arguments
        menu_name -- menu name to check if exists
        """
        menu_list = self._get_wp_json("menu list --fields=name --format=json")
        # if no existing menus
        if not menu_list:
            return False
        # Looping through existing menus
        for existing_menu in menu_list:
            if existing_menu['name'] == menu_name:
                return True
        return False

    def ensure_polylang_main_menu(self):
        """
        Ensure that main menu exists
        """
        if not self._menu_exists(self.MAIN_MENU):
            self._run_wp_cli_action("pll menu create {} top".format(self.MAIN_MENU))
