"""Type casts for Jinja 2."""


class FilterModule(object):
    def filters(self):
        return {
            'cast_to_boolean': bool
        }
