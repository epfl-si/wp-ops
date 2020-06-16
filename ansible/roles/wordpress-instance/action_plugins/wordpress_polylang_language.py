# Create or delete a Polylang language and translation ("polylang-mo")

# To be able to import wordpress_action_module
import sys
import os
sys.path.append(os.path.dirname(__file__))
from wordpress_action_module import WordPressActionModule
import json

class ActionModule(WordPressActionModule):

    locales = {
        "fr": {"name": "Français", "locale": "fr_FR", "slug": "fr", "flag": "fr"},
        "en": {"name": "English", "locale": "en_GB", "slug": "en", "flag": "gb"},
        "de": {"name": "Deutsch", "locale": "de_DE", "slug": "de", "flag": "de"},
    }

    def run(self, tmp=None, task_vars=None):
        self.result = super(ActionModule, self).run(tmp, task_vars)

        wp_veritas_languages = self._task.args.get('languages')
        desired_state = self._task.args.get('state', 'absent')

        if desired_state == "present":
            self.ensure_polylang_lang(wp_veritas_languages)
            self.ensure_polylang_mo_translations(wp_veritas_languages)
        return self.result

    def ensure_polylang_lang(self, wp_veritas_languages):

        result = None

        # get all actual languages of WP site
        actual_languages = [lang['slug'] for lang in self._get_wp_json("pll lang list --format=json")]

        # checks if parameter wp_veritas_language needs to be deleted
        for lang in actual_languages:
            found_lang_to_delete = True
            for wp_veritas_lang in wp_veritas_languages:
                if wp_veritas_lang == lang:
                    found_lang_to_delete = False
                    break
            if found_lang_to_delete:
                # delete lang present in wp-veritas but absent in actual site
                self._update_result(self._run_wp_cli_action('pll lang delete {}'.format(lang)))

        # checks if parameter wp_veritas_language needs to be created
        for wp_veritas_lang in wp_veritas_languages:
            if wp_veritas_lang not in actual_languages:
                # create lang because this lang is present in wp-veritas and absent in actual site
                # wp pll lang create <name> <language-code> <locale> [--rtl=<bool>] [--order=<int>] [--flag=<string>] [--no_default_cat=<bool>]
                result = self._run_wp_cli_action('pll lang create {name} {slug} {locale} --flag={flag}'.format(**self.locales[wp_veritas_lang]))
                self._run_wp_cli_action("pll option update media_support 0")
                self._run_wp_cli_action("pll option sync taxonomies")
                self._update_result(result)

    def ensure_polylang_mo_translations(self, wp_veritas_languages):

        # TODO: examine `wp pll lang list
        # --format=json --fields=mo_id,slug` to figure out language's mo_id
        actual_mo_languages = json.loads(self._run_wp_cli_action('pll lang list --format=json --fields=mo_id,slug')['stdout'])

        # TODO: mo_id should exist since we already went through
        # self.ensure_polylang_lang(). If that is not the case, fail with red.
        for site_lang in actual_mo_languages:
            if not site_lang['mo_id']:
                # fail with red.
                return self._update_result(False)

        # TODO: obtain current translations with `wp post meta get $mo_id
        # _pll_strings_translations --format=json`



        tagline_key = json.loads(self._run_wp_cli_action("option get blogdescription --format=json")['stdout'])
        site_title_key = json.loads(self._run_wp_cli_action("option get blogname --format=json")['stdout'])
        date_format_key = json.loads(self._run_wp_cli_action("option get date_format --format=json")['stdout'])
        time_format_key = json.loads(self._run_wp_cli_action("option get time_format --format=json")['stdout'])
        list_of_key_values_pairs = [[site_title_key, site_title_key],
                                    [tagline_key, tagline_key],
                                    [date_format_key, date_format_key],
                                    [time_format_key, time_format_key]]

        for site_lang in actual_mo_languages:
            strings_translations = json.loads(self._run_wp_cli_action('post meta get {} _pll_strings_translations --format=json'.format(site_lang['mo_id']))['stdout'])
            if len(strings_translations) < 4:
                # echo '[["CSQI", "CSQI"], ["scientific computing and uncertainty quantification", "scientific computing and uncertainty quantification"], ["d.m.Y", "d.m.Y"], ["H:i", "H:i"]]' |
                # wp post meta update 4 _pll_strings_translations --format=json
                self._run_wp_cli_action("post meta update {} _pll_strings_translations {} --format=json".format(site_lang['mo_id'], json.dumps(list_of_key_values_pairs)))





        # The structure is a translation associative array in list-of-kv-pairs
        # format. Fill out any missing entries according to the following
        # model,
        #
        # [[site_title_key, site_title_key],
        #  [tagline_key, tagline_key],
        #  [date_format_key, date_format_key],
        #  [time_format_key, time_format_key]]
        #
        # where
        #
        # tagline_key = self.run_wp_cli("option get blogdescription")
        # site_title_key = self.run_wp_cli("option get blogname")
        # date_format_key = self.run_wp_cli("option get date_format")
        # time_format_key = self.run_wp_cli("option get time_format")
        #
        # TODO: if unchanged, return green to Ansible; otherwise, save the
        # new _pll_strings_translations with
        #
        #   self.run_wp_cli("post meta update {} _pll_strings_translations --format=json".format(mo_id), pipe_input=json.dumps(list_of_kv_pairs))
        #
        # and return yellow.
        pass
