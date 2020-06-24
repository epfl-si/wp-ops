# Create or delete a Polylang language and translation ("polylang-mo")

# To be able to import wordpress_action_module
import sys
import os
import json
from ansible.errors import AnsibleError, AnsibleActionFail

sys.path.append(os.path.dirname(__file__))
from wordpress_action_module import WordPressActionModule

class ActionModule(WordPressActionModule):

    locales = {
        "fr": {"name": "Français", "locale": "fr_FR", "slug": "fr", "flag": "fr"}, # ← you can use 'ch' here to get the Swiss flag
        "en": {"name": "English", "locale": "en_US", "slug": "en", "flag": "gb"},
        "de": {"name": "Deutsch", "locale": "de_DE", "slug": "de", "flag": "de"},
        "it": {"name": "Italiano", "locale": "it_IT", "slug": "it", "flag": "it"},
        "es": {"name": "Español", "locale": "es_ES", "slug": "es", "flag": "es"},
        "ro": {"name": "Română", "locale": "ro_RO", "slug": "ro", "flag": "ro"},
        "el": {"name": "Ελληνικά", "locale": "el", "slug": "el", "flag": "gr"},
    }

    def run(self, tmp=None, task_vars=None):
        self.result = super(ActionModule, self).run(tmp, task_vars)

        desired_state = self._task.args.get('state', 'absent')
        language = self._task.args.get('language')

        self.ensure_polylang_language(language, desired_state)
        return self.result

    def ensure_polylang_language(self, language, expected_state):
        if language not in self.locales:
            raise AnsibleError('Unknown language {}'.format(language))

        current_languages = [lang['slug'] for lang in self._get_wp_json("pll lang list --format=json")]

        if expected_state == 'present' and language not in current_languages:
            self._ensure_language_exists(language)

        if expected_state == 'absent' and language in current_languages:
            self._ensure_language_deleted(language)

    def _ensure_language_exists(self, language):
        cmd = "pll lang create {name} {slug} {locale} --flag={flag}".format(**self.locales[language])
        self._run_wp_cli_action(cmd)
        if language not in self._get_polylang_languages() and language != "en":
            raise AnsibleError("FATAL: {} did not have the expected effect of creating the language - Perhaps the metadata (e.g. the flag) is wrong in wordpress_polylang_language.py?".format(cmd))

    def _ensure_language_deleted(self, language):
        self._run_wp_cli_action("pll lang delete {}".format(language))

    def _get_polylang_languages (self):
        """Returns: A dict of `mo_id`s keyed by language slug."""

        def get_moids_by_slug():
            get_cmd = 'pll lang list --format=json --fields=mo_id,slug'
            return dict([(lang["slug"], lang["mo_id"])
                         for lang in self._get_wp_json(get_cmd)])

        retval = get_moids_by_slug()
        # mo_id's are created lazily:
        if None in retval.values():
            # `wp pll option sync taxonomies` generates the mo id of
            # newly-created languages, and may or may not be doing something
            # else... Oh well
            self._run_wp_cli_action("pll option sync taxonomies", update_result=False)
            retval = get_moids_by_slug()

            # Failing again is fatal.
            if None in retval.values():
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
