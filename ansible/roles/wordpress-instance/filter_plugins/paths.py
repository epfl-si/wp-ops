"""os.path.join for Jinja 2."""

import os

class FilterModule(object):
    def filters(self):
        return {
            'joinpath': self.joinpath
        }

    def joinpath(self, piped, basepath):
        return os.path.join(basepath, piped)
