import os
import subprocess
import datetime
import logging
import json

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

      class ApiClientForJsonPatch(client.ApiClient):
          """As seen in https://github.com/kubernetes-client/python/issues/1216#issuecomment-691116322"""
          def call_api(self, resource_path, method,
                       path_params=None, query_params=None, header_params=None,
                       body=None, post_params=None, files=None,
                       response_type=None, auth_settings=None, async_req=None,
                       _return_http_data_only=None, collection_formats=None,
                       _preload_content=True, _request_timeout=None):
              header_params['Content-Type'] = self.select_header_content_type(['application/json-patch+json'])
              return super().call_api(resource_path, method, path_params, query_params, header_params, body,
                                      post_params, files, response_type, auth_settings, async_req, _return_http_data_only,
                                      collection_formats, _preload_content, _request_timeout)

      self._custom_jsonpatch = client.CustomObjectsApi(ApiClientForJsonPatch())

  @classproperty
  def custom(cls):
    return cls.__get()._custom

  @classproperty
  def custom_jsonpatch(cls):
    return cls.__get()._custom_jsonpatch

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
            ingresses = get_custom_resource_items(
                "networking.k8s.io", "v1", "ingresses")
            wordpresssites = get_custom_resource_items(
                cls._group, cls._version, cls._plural)
        except ApiException:
            logging.exception("when calling CustomObjectsApi->list_namespaced_custom_object")
            return []

        bag_ingress = BagOfIngresses(ingresses)
        bag_wp = BagOfWordpressSites(wordpresssites)

        ret = []
        for uid, ingress in bag_ingress.items():
            wp = bag_wp.lookup(uid)
            ret.append(cls(wp=wp, ingress=ingress))

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
            self._patch_wordpresssite_status()
            self._pushgateway.record_success(self)
        except Exception:
            logging.exception("Error running wp cron")
            self._pushgateway.record_failure(self)

    def _do_run_cron(self):
        cmdline = ['wp', f'--ingress={self._ingress_name()}', 'cron', 'event', 'run', '--due-now']
        self._do_run_wp(cmdline)

    def _do_run_wp(self, cmdline, **kwargs):
        if 'DEBUG' in os.environ:
            cmdline.insert(0, 'echo')
        return subprocess.run(cmdline, check=True, **kwargs)

    def _patch_wordpresssite_status (self):
        """
        Patch the Wordpresssite CR status with:
            lastCronJobRuntime: The last cron job run time
            plugins: The active plugins on the site
        """
        try:
            KubernetesAPI.custom_jsonpatch.patch_namespaced_custom_object_status(
                group=self._group,
                version=self._version,
                plural=self._plural,
                namespace=self._namespace,
                name=self._wp['metadata']['name'],
                body=[
                    {
                        "op": "add",
                        "path": "/status/wordpresssite",
                        "value": self._status_wordpresssite_struct()
                    }
                ])
        except ApiException:
            logging.exception("when calling CustomObjectsApi->patch_namespaced_custom_object_status")
            raise

    def _status_wordpresssite_struct(self):
        if 'DEBUG' in os.environ:
            out = {'plugins': {'toto': {}, 'tutu': {}}}
        else:
            cmdline = ['wp', f'--ingress={self._ingress_name()}', 'eval', '''echo(json_encode(apply_filters('wp_operator_status',[]), JSON_PRETTY_PRINT));''']
            result = self._do_run_wp(cmdline, capture_output=True, text=True)
            out = json.loads(result.stdout)
            if out == []:
                out = {}
        return {
            'lastCronJobRuntime': datetime.datetime.now().isoformat(),
            **out
        }


