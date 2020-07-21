"""'Short-circuit roles with tags' feature.

When `ansible_run_tags | any_known_tag(role_path)` is
False, we can (and should) skip the entire role. This lets role
authors employ `tags: always` when they don't really mean it.
"""

import yaml
import os
from ansible.module_utils import six

class FilterModule(object):
    def filters(self):
        return {
            'any_known_tag': self.any_known_tag,
            'find_all_tags': self.find_all_tags
        }

    def any_known_tag(self, tags, role_path):
        tags = set(tags)
        if 'all' in tags:  # i.e., no tags
            return True
        else:
            return bool(
                tags.intersection(set(self.find_all_tags(role_path))))

    def find_all_tags(self, role_path):
        return list(_TagShaker.of(os.path.join(role_path, 'tasks')).get_role_tags())

class _TagShaker(object):
    _instances = {}
    @classmethod
    def of(cls, templates_path):
        if templates_path not in cls._instances:
            cls._instances[templates_path] = cls(templates_path)
        return cls._instances[templates_path]

    def __init__(self, templates_path):
        self._tasks_path = templates_path

    def get_role_tags(self):
        if not hasattr(self, '_role_tags_cached'):
            self._role_tags_cached = self._walk_all_role_tags()
        return self._role_tags_cached

    def _walk_all_role_tags(self):
        for parentdir, subdirs, files in os.walk(self._tasks_path):
            for filename in files:
                if filename.startswith('.') or filename.endswith('~'):
                    continue
                try:
                    parsed = yaml.safe_load(open(os.path.join(parentdir, filename)))
                except Exception:
                    continue
                if type(parsed) is not list:
                    continue
                for task in parsed:
                    if type(task) is not dict:
                        continue
                    if 'tags' not in task:
                        continue
                    tags = task['tags']
                    if isinstance(tags, six.string_types):
                        tags = [tags]
                    if type(tags) is list:
                        for tag in tags:
                            if tag not in ('always', 'never'):
                                yield tag
