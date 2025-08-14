import logging
import os

from kubernetes.client.exceptions import ApiException

from kubernetes import client, config


class classproperty:
    def __init__(self, func):
        self.fget = func
    def __get__(self, instance, owner):
        return self.fget(owner)


class KubernetesAPI:
    __singleton = None

    @classmethod
    def __get(cls):
        if cls.__singleton is None:
            cls.__singleton = cls()

        return cls.__singleton

    def __init__(self):
        config.load_config()

        self._custom = client.CustomObjectsApi()

    @classproperty
    def custom(cls):
        return cls.__get()._custom


class _BagBase:
    def __init__(self, items):
        self._bag = {}
        for i in items:
            self.add(i)

    def lookup(self, uid):
        return self._bag[uid]

    def items(self):
        return self._bag.items()

    def keys(self):
        return self._bag.keys()

    def values(self):
        return self._bag.values()


class BagOfWordpressSites (_BagBase):
    def add(self, wp):
        uid = wp['metadata']['uid']
        self._bag[uid] = wp


class BagOfDatabases (_BagBase):
    def add(self, database):
        if (database['metadata'].get('ownerReferences')):
            owner_uid = database['metadata']['ownerReferences'][0]['uid']
            self._bag[owner_uid] = database

class BagOfBackups (_BagBase):
    def add(self, backup):
        mariadb_ref = backup['spec']['mariaDbRef']['name']
        self._bag[mariadb_ref] = backup

class WordpressSite:

    _namespace = os.getenv('K8S_NAMESPACE')
    _group = "wordpress.epfl.ch"
    _version = "v2"
    _plural = "wordpresssites"

    @classmethod
    def all (cls):
        def get_custom_resource_items (group, version, plural):
            api_response = KubernetesAPI.custom.list_namespaced_custom_object(group, version, cls._namespace, plural)
            return api_response['items']

        try:
            backups = get_custom_resource_items("k8s.mariadb.com", "v1alpha1", "backups")
            databases = get_custom_resource_items("k8s.mariadb.com", "v1alpha1", "databases")
            wordpresssites = get_custom_resource_items(cls._group, cls._version, cls._plural)
        except ApiException:
            logging.exception("when calling CustomObjectsApi->list_namespaced_custom_object")
            return []

        bag_backups = BagOfBackups(backups)
        bag_database = BagOfDatabases(databases)
        bag_wp = BagOfWordpressSites(wordpresssites)

        ret = []
        for uid, database in bag_database.items():
            wp = bag_wp.lookup(uid)
            backup = bag_backups.lookup(database['spec']['mariaDbRef']['name'])
            ret.append(cls(wp=wp, database=database, backup=backup))

        return ret

    def __init__(self, database, wp, backup):
        self._database = database
        self._wp = wp
        self._backup = backup

    @property
    def moniker (self):
        return f"{self._wp['metadata']['name']}"

    @property
    def database_name (self):
        return self._database['metadata']['name']

    @property
    def mariadb_name (self):
        return self._backup['spec']['mariaDbRef']['name']
