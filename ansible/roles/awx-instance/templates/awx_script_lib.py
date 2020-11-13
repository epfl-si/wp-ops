import sys
import six
from django.db import transaction
from awx.main.utils import decrypt_value, get_encryption_key
from cryptography.fernet import InvalidToken

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

        if isinstance(value, self.__class__):
            value = value.__obj

        if not self.__is_unchanged(name, value):
            setattr(self.__obj, name, value)
            update_json_status(changed=True)

    def __is_unchanged (self, field, newvalue):
        if field == 'inputs':
            if type(newvalue) is not dict:
                return False
            for k in newvalue.keys():
                if not self.__is_unchanged_input(k, newvalue):
                    return False
                return True
        else:
            oldvalue = getattr(self.__obj, field, None)
            return _is_same_value(oldvalue, newvalue,
                                  get_encryption_key(field, self.__obj.pk))

    def __is_unchanged_input (self, k, newvalue):
        # Some fields of 'inputs' are encrypted; retrieve the
        # original values using the .get_input() accessor
        try:
            oldv = self.__obj.get_input(k)
        except InvalidToken:    # Field is not decipherable
            return False
        except AttributeError:  # Field doesn't exist (yet)
            return False

        return _is_same_value(oldv, newvalue[k])


def _is_same_value(a, b, decryption_key=None):
    if a is b:
        return True
    if a == b:
        return True

    if isinstance(b, six.string_types):
        if isinstance(a, bytes):
            return _is_same_value(bytes(a, 'utf-8'), b)
        if not isinstance(a, six.string_types):
            return False

        if decryption_key:
            did_decrypt = False
            if a.startswith('$encrypted$'):
                did_decrypt = True
                a = decrypt_value(decryption_key, a)
            if b.startswith('$encrypted$'):
                did_decrypt = True
                b = decrypt_value(decryption_key, b)
            if did_decrypt:
                return _is_same_value(a, b)

    return False

class AnsibleGetOrCreate:
    save_queue = []
    nesting = 0

    def __init__(self, clazz, **get_or_create_kwargs):
        self._obj_class = clazz
        self._get_or_create_kwargs = get_or_create_kwargs

    def __enter__(self):
        self._txn = transaction.atomic()
        self._txn.__enter__()
        self.__class__.nesting += 1

        try:
            return self._begin()
        except Exception as e:
            self.__exit__(*sys.exc_info())
            raise e

    def __exit__(self, type, value, tb):
        self.__class__.nesting -= 1
        try:
            if not tb:
                self._commit_unless_check_mode()
            self._txn.__exit__(type, value, tb)
            if self.__class__.nesting == 0:
                for obj in reversed(self.__class__.save_queue):
                    obj.save()
        except Exception as e:
            self._txn.__exit__(*sys.exc_info())
            raise e

    def _begin(self):
        try:
            self._obj = self._obj_class.objects.get(
                **self._get_or_create_kwargs)
            self._created = False
        except self._obj_class.DoesNotExist:
            self._obj = self._obj_class(**self._get_or_create_kwargs)
            self._created = True

        update_json_status(changed=self._created)
        return AnsibleDjangoObserver(self._obj)

    def _commit_unless_check_mode(self):
        if check_mode:
            if self._created:
                self._obj.delete()
        else:
            # We need to save objects in the same order they
            # were created (otherwise foreign-key relationships
            # will be unable to find new objects' IDs)
            self.__class__.save_queue.append(self._obj)
