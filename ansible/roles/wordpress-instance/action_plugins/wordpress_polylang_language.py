# Create or delete a Polylang language and translation ("polylang-mo")

# To be able to import wordpress_action_module
import sys
import os
import json
from ansible.errors import AnsibleActionFail

sys.path.append(os.path.dirname(__file__))
from wordpress_action_module import WordPressActionModule

class ActionModule(WordPressActionModule):

    locales = {
        "fr": {"name": "Français", "locale": "fr_FR", "slug": "fr", "flag": "fr"},
        "en": {"name": "English", "locale": "en_GB", "slug": "en", "flag": "gb"},
        "de": {"name": "Deutsch", "locale": "de_DE", "slug": "de", "flag": "de"},
    }

    def run(self, tmp=None, task_vars=None):
        self.result = super(ActionModule, self).run(tmp, task_vars)

        expected_languages = self._task.args.get('languages')
        desired_state = self._task.args.get('state', 'absent')

        if desired_state == "present":
            self.ensure_polylang_lang(expected_languages)
            self.ensure_polylang_mo_translations()
        return self.result

    def ensure_polylang_lang(self, expected_languages):

        result = None

        # get all actual languages of WP site
        actual_languages = [lang['slug'] for lang in self._get_wp_json("pll lang list --format=json")]

        # checks if parameter lang needs to be deleted
        for lang in actual_languages:
            found_lang_to_delete = True
            for expected_lang in expected_languages:
                if expected_lang == lang:
                    found_lang_to_delete = False
                    break
            if found_lang_to_delete:
                # delete lang present in wp-veritas but absent in actual site
                self._run_wp_cli_action("pll lang delete {}".format(lang))

        # checks if parameter expected_lang needs to be created
        for expected_lang in expected_languages:
            if expected_lang not in actual_languages:
                # create lang because this lang is present in wp-veritas and absent in actual site
                self._run_wp_cli_action("pll lang create {name} {slug} {locale} --flag={flag}".format(**self.locales[expected_lang]))

        media_support_before = self._run_wp_cli_action("pll option get media_support", update_result=False)['stdout']
        if int(media_support_before) != 0:
            self._update_result(self._run_wp_cli_action("pll option update media_support 0"))

        # command "pll option sync taxonomies" generate the mo id of new lang and may be doing something else...
        self._run_wp_cli_action("pll option sync taxonomies", update_result=False)

    def ensure_polylang_mo_translations(self):

        actual_mo_languages = json.loads(self._run_wp_cli_action('pll lang list --format=json --fields=mo_id,slug', update_result=False)['stdout'])

        # Check if mo_id exist since we already went through self.ensure_polylang_lang()
        for site_lang in actual_mo_languages:
            if not site_lang['mo_id']:
                raise AnsibleActionFail("Cannot find the mo_id of lang '{}' - Error: method 'ensure_polylang_mo_translations()' ".format(site_lang["slug"]))

        tagline_key = json.loads(self._run_wp_cli_action("option get blogdescription --format=json", update_result=False)['stdout'])
        site_title_key = json.loads(self._run_wp_cli_action("option get blogname --format=json", update_result=False)['stdout'])
        date_format_key = json.loads(self._run_wp_cli_action("option get date_format --format=json", update_result=False)['stdout'])
        time_format_key = json.loads(self._run_wp_cli_action("option get time_format --format=json", update_result=False)['stdout'])

        # The structure is a translation associative array in list-of-kv-pairs format.
        # Fill out any missing entries according to the following model
        list_of_key_values_pairs = [[site_title_key, site_title_key],
                                    [tagline_key, tagline_key],
                                    [date_format_key, date_format_key],
                                    [time_format_key, time_format_key]]

        for site_lang in actual_mo_languages:
            strings_translations = json.loads(self._run_wp_cli_action('post meta get {} _pll_strings_translations --format=json'.format(site_lang['mo_id']), update_result=False)['stdout'])
            if len(strings_translations) < 4:
                self._run_wp_cli_action("post meta update {} _pll_strings_translations --format=json".format(site_lang['mo_id']), pipe_input=json.dumps(list_of_key_values_pairs))
