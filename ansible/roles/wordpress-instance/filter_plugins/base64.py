"""Base64 helpers."""

from base64 import b64encode

class FilterModule(object):
    def filters(self):
        return {
            'base64_values': self.base64_values
        }
    def base64_values(self, d):
        return dict((k, b64encode(bytes(v, 'utf-8'))) for k, v in d.items())
