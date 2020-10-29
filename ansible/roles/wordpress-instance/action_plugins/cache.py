from ansible.module_utils import six
import collections
import inspect
import os
import pickle
import shutil

class _DecoratorCache(object):
    def __init__(self_, cache):
        self_.__cache = cache

    def by(self_, key_f):
        def decorator(f):
            def wrapped_f(self, *args, **kwargs):
                cache_key = self_.__get_key(key_f, self, *args, **kwargs)
                if not self_.__cache.has(cache_key):
                    self_.__cache.set(cache_key, f(self, *args, **kwargs))
                return self_.__cache.get(cache_key)

            wrapped_f.__name__ = f.__name__  # YAGNI?
            return wrapped_f
        return decorator

    def invalidate_by_prefix(self_, key_f):
        def decorator(f):
            def wrapped_f(self, *args, **kwargs):
                self_.__cache.invalidate_prefix(self_.__get_key(key_f, self, *args, **kwargs))
                return f(self, *args, **kwargs)

            wrapped_f.__name__ = f.__name__
            return wrapped_f
        return decorator

    @staticmethod
    def __get_key(key_f, self, *args, **kwargs):
        if len(inspect.signature(key_f).parameters) > 1:
            # Either the decorator's lambda parameter only takes self, or it
            # has to swallow the entire set of arguments to the method. This
            # is not JavaScript. There are rules.
            key_raw = key_f(self, *args, **kwargs)
        else:
            key_raw = key_f(self)

        def hashable(k):
            return k if hasattr(k, '__hash__') else json.dumps(k)

        if isinstance(key_raw, tuple):
            return tuple(hashable(k) for k in key_raw)
        else:
            return hashable(key_raw)


class _InMemoryPrefixCache(object):
    def __init__(self):
        self.__contents = {}

    def has(self, key):
        return key in self.__contents

    def get(self, key):
        return self.__contents.get(key)

    def set(self, key, value):
        self.__contents[key] = value

    def invalidate_prefix(self, key_prefix):
        for k in list(self.__contents):  # Because Python, to put it bluntly, sucks.
                                         # https://stackoverflow.com/a/11941855/435004
            if self.__is_prefix(key_prefix, k):
                del self.__contents[k]

    @staticmethod
    def __is_prefix(a, b):
        if isinstance(a, six.string_types) and isinstance(b, six.string_types):
            return b.startswith(a)
        elif isinstance(a, tuple) and isinstance(b, tuple):
            for i in range(len(a)):
                if a[i] != b[i]:
                    return False
            return True
        else:
            return False


class _OnDiskPrefixCache(object):
    def __init__(self, path):
        self._path = path
        os.makedirs(path, exist_ok=True)

    def has(self, key):
        return os.path.exists(self._key_path(key))

    def get(self, key):
        with open(self._key_path(key), 'rb') as f:
            return pickle.load(f)

    def set(self, key, value):
        key_path = self._key_path(key)
        os.makedirs(os.path.dirname(key_path), exist_ok=True)
        with open(key_path, 'wb') as f:
            pickle.dump(value, f)

    def invalidate_prefix(self, key_prefix):
        shutil.rmtree(self._key_path(key_prefix))

    def _key_path(self, key):
        def as_path_component(k):
            if isinstance(k, six.string_types):
                return k
            else:
                return json.dumps(k)

        return os.path.join(
            self._path,
            *(as_path_component(k) for k in key))


def InMemoryDecoratorCache():
    return _DecoratorCache(_InMemoryPrefixCache())

def OnDiskDecoratorCache(topdir):
    return _DecoratorCache(_OnDiskPrefixCache(topdir))
