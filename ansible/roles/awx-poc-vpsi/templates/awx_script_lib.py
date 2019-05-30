import six
import sys
from django.db import transaction


class AnsibleDjangoObserver:
    def __init__(self, obj):
        self.__obj = obj

    def __getattr__(self, name):
        if name.endswith("__obj"):
            return object.__getattr__(self, name)

        return getattr(self.__obj, name)

    def __setattr__(self, name, value):
        if name.endswith("__obj"):
            return object.__setattr__(self, name, value)
            
        oldvalue = getattr(self.__obj, name, None)
        if oldvalue != value:
            setattr(self.__obj, name, value)
            update_json_status(changed=True)


class AnsibleGetOrCreate:
    def __init__(self, clazz, **get_or_create_kwargs):
        self._obj_class = clazz
        self._get_or_create_kwargs = get_or_create_kwargs

    def __enter__(self):
        self._txn = transaction.atomic()
        self._txn.__enter__()

        try:
            return self._begin()
        except Exception as e:
            self.__exit__(*sys.exc_info())
            raise e

    def __exit__(self, type, value, tb):
        try:
            if not tb:
                self._commit_unless_check_mode()
            self._txn.__exit__(type, value, tb)
        except Exception as e:
            self._txn.__exit__(*sys.exc_info())
            raise e

    def _begin(self):
        self._obj, self._created = self._obj_class.objects.get_or_create(
            **self._get_or_create_kwargs)
        update_json_status()
        return AnsibleDjangoObserver(self._obj)

    def _commit_unless_check_mode(self):
        if check_mode:
            if self._created:
                self._obj.delete()
        else:
            self._obj.save()
