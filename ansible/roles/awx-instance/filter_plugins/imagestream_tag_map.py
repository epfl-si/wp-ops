import json
from ansible.module_utils import six

class FilterModule(object):
    '''
    custom jinja2 filter to extract the current versions of an ImageStream as a dict.
    '''

    def filters(self):
        return {
            'imagestream_tag_map': self.imagestream_tag_map
        }

    def imagestream_tag_map(self, struct):
        if isinstance(struct, six.string_types):
            struct = json.loads(struct)
        return dict([u['tag'], self._get_latest_version(u)] for u in struct.get('status', {}).get('tags', []))

    def _get_latest_version(self, u):
        try:
            return u['items'][0]['image']
        except KeyError:
            return None
        except IndexError:
            return None

