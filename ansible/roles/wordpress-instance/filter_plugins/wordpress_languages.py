"""Sort languages in canonical order.

This is a hack to ensure that "important" languages (i.e. French and English)
get created first, and therefore become Polylang's default language.
"""

class FilterModule(object):
    def filters(self):
        return { "languages_in_order": self.languages_in_order }

    def languages_in_order(self, languages):
        """
        :return: 'en' first, 'fr' second
        """
        def partition(pred, iterable):
            """
            https://stackoverflow.com/a/4578605/435004
            """
            trues = []
            falses = []
            for item in iterable:
                if pred(item):
                    trues.append(item)
                else:
                    falses.append(item)
            return trues, falses

        english, other = partition(lambda lang: lang == 'en', languages)
        french, other = partition(lambda lang: lang == 'fr', other)
        return english + french + other
