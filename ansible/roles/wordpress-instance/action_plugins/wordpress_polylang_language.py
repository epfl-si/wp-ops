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

    def ensure_polylang_mo_translations(self):
        """Ensure that every language has a so-called "polylang_mo" translation table.

        If that is not the case, create a dummy one.
        """
        for site_lang in self._get_polylang_languages():
            strings_translations = self._get_wp_json('post meta get {} _pll_strings_translations --format=json'.format(site_lang['mo_id']))
            if len(strings_translations) < 4:
                self._run_wp_cli_action("post meta update {} _pll_strings_translations --format=json".format(site_lang['mo_id']), pipe_input=json.dumps(self._get_dummy_translation_table()))

    def _get_polylang_languages (self):
        """Returns: A list of dicts with fields `slug` and `mo_id`"""
        get_cmd = 'pll lang list --format=json --fields=mo_id,slug'
        retval = self._get_wp_json(get_cmd)

        # mo_id's are created lazily:
        if [lang for lang in retval if not lang.get('mo_id')]:
            # `wp pll option sync taxonomies` generates the mo id of
            # newly-created languages, and may or may not be doing something
            # else... Oh well
            self._run_wp_cli_action("pll option sync taxonomies", update_result=False)
            retval = self._get_wp_json(get_cmd)

            # Failing again is fatal.
            for lang in retval:
                if not lang.get('mo_id'):
                    raise AnsibleActionFail("Cannot find the mo_id of lang '{}'".format(lang["slug"]))

        return retval

    def _get_dummy_translation_table (self):
        if not hasattr(self, '_cached_dummy_translation_table'):
            tagline_key = self._get_wp_json("option get blogdescription --format=json")
            site_title_key = self._get_wp_json("option get blogname --format=json")
            date_format_key = self._get_wp_json("option get date_format --format=json")
            time_format_key = self._get_wp_json("option get time_format --format=json")

            self._cached_dummy_translation_table = [[site_title_key, site_title_key],
                                        [tagline_key, tagline_key],
                                        [date_format_key, date_format_key],
                                        [time_format_key, time_format_key]]
        return self._cached_dummy_translation_table
