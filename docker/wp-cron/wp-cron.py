import os
import time
from pprint import pprint

from kubernetes import client, config
from kubernetes.dynamic import DynamicClient
from kubernetes.client.exceptions import ApiException


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
      self._core = client.CoreV1Api()
      self._extensions = client.ApiextensionsV1Api()
      self._dynamic = DynamicClient(client.ApiClient())
      self._networking = client.NetworkingV1Api()

  @classproperty
  def custom(cls):
    return cls.__get()._custom

  @classproperty
  def core(cls):
    return cls.__get()._core

  @classproperty
  def extensions(cls):
    return cls.__get()._extensions

  @classproperty
  def dynamic(cls):
    return cls.__get()._dynamic

  @classproperty
  def networking(cls):
    return cls.__get()._networking


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


class BagOfIngresses (_BagBase):
    def add(self, ingress):
        if (ingress['metadata'].get('ownerReferences')):
            owner_uid = ingress['metadata']['ownerReferences'][0]['uid']
            self._bag[owner_uid] = ingress


def get_wordpress_sites():
    group = "wordpress.epfl.ch"
    version = "v2"
    namespace = os.getenv('K8S_NAMESPACE')
    plural = "wordpresssites"
    api_response = KubernetesAPI.custom.list_namespaced_custom_object(group, version, namespace, plural)
    return api_response['items']


def get_ingresses():
    group = "networking.k8s.io"
    version = "v1"
    namespace = os.getenv('K8S_NAMESPACE')
    plural = "ingresses"
    api_response = KubernetesAPI.custom.list_namespaced_custom_object(group, version, namespace, plural)
    return api_response['items']


if __name__ == '__main__':
    try:
        ingresses = get_ingresses()
        wordpresssites = get_wordpress_sites()
        bag_ingress = BagOfIngresses(ingresses)
        bag_wp = BagOfWordpressSites(wordpresssites)

        for uid, ingress in bag_ingress.items():
            wp = bag_wp.lookup(uid)
            print(f"{ingress['metadata']['name']} -> {wp['metadata']['name']}")

    except ApiException as e:
        print("Exception when calling CustomObjectsApi->list_namespaced_custom_object: %s\n" % e, flush=True)

    print("All done. I am going to sleep", flush=True)
    time.sleep(3600)
