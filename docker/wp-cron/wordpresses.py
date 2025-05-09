import os
import subprocess

from kubernetes import client, config
from kubernetes.dynamic import DynamicClient
from kubernetes.client.exceptions import ApiException

from pushgateway import Pushgateway

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


class WordpressSite:
    @classmethod
    def all (cls):
        def get_custom_resource_items (group, version, plural):
            namespace = os.getenv('K8S_NAMESPACE')
            api_response = KubernetesAPI.custom.list_namespaced_custom_object(group, version, namespace, plural)
            return api_response['items']

        try:
            ingresses = get_custom_resource_items(
                "networking.k8s.io", "v1", "ingresses")
            wordpresssites = get_custom_resource_items(
                "wordpress.epfl.ch", "v2", "wordpresssites")
        except ApiException as e:
            print("Exception when calling CustomObjectsApi->list_namespaced_custom_object: %s\n" % e, flush=True)
            return []

        bag_ingress = BagOfIngresses(ingresses)
        bag_wp = BagOfWordpressSites(wordpresssites)

        ret = []
        for uid, ingress in bag_ingress.items():
            wp = bag_wp.lookup(uid)
            ret.append(cls(wp, ingress))

        return ret

    def __init__(self, ingress, wp):
        self._ingress = ingress
        self._wp = wp
        self._pushgateway = Pushgateway("pushgateway:9091")

    def set_pushgateway(self, host_port):
        self._pushgateway = Pushgateway(host_port)

    @property
    def moniker (self):
        return f"{self._wp['metadata']['name']}"

    def _ingress_name(self):
        return self._ingress['metadata']['name']

    def run_cron(self):
        self._pushgateway.record_start(self)
        try:
            self._do_run_cron()
            self._pushgateway.record_success(self)
        except Exception as e:
            print(e)
            self._pushgateway.record_failure(self)

    def _do_run_cron(self):
        try:
            cmdline = ['wp', f'--ingress={self._ingress_name()}', 'cron', 'event', 'run', '--due-now']
            if 'DEBUG' in os.environ:
                cmdline.insert(0, 'echo')
            subprocess.run(cmdline, check=True)
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error running wp cron: {e}")
            return False
