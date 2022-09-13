"""URL filters."""

import re

class FilterModule(object):
    def filters(self):
        return {
            'url_quote': self.url_quote,
            'ensure_trailing_slash': self.ensure_trailing_slash
        }

    def url_quote(self, url):
        return re.sub(r'([/\\])', r'\\\1', url)

    def ensure_trailing_slash(self, url):
        if not url.endswith("/"):
            url = url + "/"
        return url