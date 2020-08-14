"""URL filters."""

import re

class FilterModule(object):
    def filters(self):
        return {
            'url_quote': self.url_quote
        }

    def url_quote(self, url):
        return re.sub(r'([/\\])', r'\\\1', url)
