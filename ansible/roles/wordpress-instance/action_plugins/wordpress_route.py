# -*- coding: utf-8 -*-

# There is a name clash with a module in Ansible named "copy":
deepcopy = __import__('copy').deepcopy
import re
import sys
import os.path
import json
import subprocess
from urllib.parse import urlparse

# To be able to import wordpress_action_module
sys.path.append(os.path.dirname(__file__))

from ansible.module_utils import six
from wordpress_action_module import WordPressPluginOrThemeActionModule

class ActionModule(WordPressPluginOrThemeActionModule):
    def run (self, tmp=None, task_vars=None):

        self.result = super(ActionModule, self).run(tmp, task_vars)

        site_url = self._task.args.get('site_url')
        self._site_name = urlparse(site_url).netloc.replace(".epfl.ch", "")
        self._openshift_env = self._task.args.get('openshift_env')

        cmd = self.get_command()

        if not self.check_route_exist():
          
          subprocess.check_output(
              cmd,
              shell=True, encoding='utf-8')

          self.result['changed'] = True
        
        return self.result

    def check_route_exist(self):

      route_name = f"httpd-{self._site_name}"
      cmd = f"oc -n wwp-test get routes {route_name} --no-headers | awk '{{print $1;}}'"

      result = subprocess.check_output(
            cmd,
            shell=True, encoding='utf-8').rstrip('\n')

      return result == route_name

    def get_command(self):

        yaml_content = f"""
              apiVersion: v1
              kind: Route
              metadata:
                annotations:
                  haproxy.router.openshift.io/balance: roundrobin
                labels:
                  app: httpd-{self._openshift_env}
                name: httpd-{self._site_name}
              spec:
                host: {self._site_name}.epfl.ch
                port:
                  targetPort: http
                tls:
                  insecureEdgeTerminationPolicy: Redirect
                  termination: edge
                to:
                  kind: Service
                  name: varnish-varnish
                  weight: 100
                wildcardPolicy: None
          """

        command = 'echo "' + yaml_content + '"' + " | oc -n wwp-test create -f -" 
        return command
