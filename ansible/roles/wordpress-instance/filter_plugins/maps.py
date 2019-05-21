"""Sometimes, you do have to program for Ansible to do your bidding."""

from jinja2.utils import soft_unicode


def map_format(pattern, values):
    """
    Apply python string formatting on an object:
    .. sourcecode:: jinja
        {{ "%s - %s"|map_format([["Hello?", "Foo!"]]) }}
            -> Hello? - Foo!
    """
    return [soft_unicode(pattern) % v for v in values]


class FilterModule(object):
    ''' jinja2 filters '''

    def filters(self):
        return {
            'map_format': map_format
        }
