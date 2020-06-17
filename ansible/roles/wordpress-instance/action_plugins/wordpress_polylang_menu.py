# Ensure that every languages has a menu located in "Top" location.
#  - if yes, do not touch anything (e.g. ic)
#  - if not, spread the jam in order that the site has a menu — it's most likely happening when creating a new site
#
# Quick test: ./wpsible -t wp.menus.polylang -l test_migration_wp__labs__bbb -e '{ "wp_destructive": { "test_migration_wp__labs__bbb" : ["config", "code"] }}'

import sys
import os
import json
from ansible.errors import AnsibleActionFail

# To be able to import wordpress_action_module
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

    # Ensure that a menu exists for each languages
    def ensure_polylang_menu(self):

        activated_theme_name = self._run_wp_cli_action("theme list --status=active --field=name", update_result=False)['stdout']

        polylang_options = self._get_wp_json("option get polylang --format=json")

        if 'nav_menus' in polylang_options and activated_theme_name in polylang_options['nav_menus'] and "top" in polylang_options['nav_menus'][activated_theme_name]:
            # This site already have a menu assigned to the "top" location, check that it is the case for all languages
            actual_languages = [lang['slug'] for lang in self._get_wp_json("pll lang list --format=json")]
            for actual_lang in actual_languages:
                if actual_lang in polylang_options['nav_menus']['epfl_master']['top']:
                    pass
                else:
                    # create menu for actual lang
                    pass
        else:
            # This site doesn't have a menu assigned to the "top" location!
            # TODO: Create all TOP menus
            # create menus if they don't exist, assuming that `wp menu location list` has a "top" menu, which is the default
            # `wp pll menu create Main top`
            if not self._menu_exists(self.MAIN_MENU):
                # TODO: return yellow if created
                self._run_wp_cli_action("pll menu create {} top".format(self.MAIN_MENU))

            if not self._menu_exists(self.FOOTER_MENU):
                # TODO: discuss if the footer_nav menu is still needed, as users can not revert it
                # TODO: return yellow if created
                self._run_wp_cli_action("pll menu create {} footer_nav".format(self.FOOTER_MENU))

            # wp option get polylang
            # wp menu item add-post Main 2 --title="Tmp Sample Page"
            # ToDo
            # 1) wp option pluck polylang nav_menus --format=json
            # 2) Fusionner la structure ainsi obtenue avec ce qu'on souhaite fixer (interpréter la chaîne vide comme []; ⚠️ en PHP il n'y a pas de différence entre [] et {})
            # 3) wp option patch insert polylang nav_menus '{"wp-theme-2018": {"fr": 6, "en": 4} }' --format=json