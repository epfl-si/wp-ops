# Create or delete a Polylang language and translation ("polylang-mo")

# To be able to import wordpress_action_module
sys.path.append(os.path.dirname(__file__))
from wordpress_action_module import WordPressActionModule


class ActionModule(WordPressActionModule):
    def run(self, tmp=None, task_vars=None):
        language = self._task.args.get('language')
        desired_state = self._task.args.get('state', 'absent')
        self.ensure_polylang_lang(language, state)
        if state == "present":
            self.ensure_polylang_mo_translations(language)

    def ensure_polylang_lang(self, language, state):
        # TODO: parse `wp pll lang list` to figure out current state
        # TODO: act w/ wp pll lang <create|delete> (for create, see parameters
        # at
        # https://github.com/diggy/polylang-cli/blob/master/README.md#wp-pll-lang-create
        # ; this module will therefore have to contain a table of all supported
        # languages, with the corresponding creation parameters) TODO: respect
        # Ansible's green/yellow!
        pass

    def ensure_polylang_mo_translations(self, language):
        # TODO: examine `wp pll lang list
        # --format=json --fields=mo_id,slug` to figure out language's mo_id
        #
        # TODO: mo_id should exist since we already went through
        # self.ensure_polylang_lang(). If that is not the case, fail with red.
        #
        # TODO: obtain current translations with `wp post meta get $mo_id
        # _pll_strings_translations --format=json`
        #
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
