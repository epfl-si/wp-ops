#-*- coding: utf-8 -*-

"""Toolbelt of Jinja filters for the wordpress-openshift_namespace role."""


def maplookup(l, lookup):
    """Look up all elements of a sequence in a dict-valued variable."""
    return [lookup[i] for i in l]


def join_lines(lines):
    """Joins `lines` with newlines and returns a single string.

    You would think you could do that with

        | join("\n")

    but you can't — see https://github.com/debops/ansible-sshkeys/issues/4
    """
    return ''.join("%s\n" % l for l in lines)


def trim_lines(text):
    return ''.join('%s\n' % l.strip() for l in text.splitlines())


class FilterModule(object):
    def filters(self):
        return {
            'maplookup':  maplookup,
            'join_lines': join_lines,
            'trim_lines': trim_lines
        }
