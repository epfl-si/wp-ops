# -*- coding: utf-8 -*-

import sys
import os.path
import subprocess
from urllib.parse import urlparse
from route_helper import check_route_exist, getRouteName

# To be able to import wordpress_action_module
sys.path.append(os.path.dirname(__file__))

from ansible.module_utils import six
from wordpress_action_module import WordPressActionModule


class ActionModule(WordPressActionModule):

    def run (self, tmp=None, task_vars=None):

        self.result = super(ActionModule, self).run(tmp, task_vars)
        
        self._openshift_env = self._task.args.get('openshift_env')
        site_url = self._task.args.get('site_url')
        self._route_name = getRouteName(site_url, self._openshift_env)
        self._hostname = urlparse(site_url).netloc
        self._openshift_namespace = self._task.args.get('openshift_namespace')
        
        # Note: 
        # La gestion des routes des différents pods -
        # à savoir subdomains-lite, www, inside, www2018, unmanaged, etc -
        # est prise en compte.
        # - Pour les routes subdomains redirection: 
        # TODO: Ajouter tous les sites dans la source de vérité + recréer les routes non conformes 
        # Exemple: https://lifev.org => httpd-lifev-org au lieu de l'actuel httpd-lifev
        # - Pour les routes 'Archives':
        # On ne les gère car fin des archives en 1 Octobre 2020

        if not check_route_exist(self._openshift_namespace, self._route_name):          
          subprocess.check_output(
              self._get_create_route_command(),
              shell=True, encoding='utf-8')

          self.result['changed'] = True
        
        return self.result

    def _get_create_route_command(self):
        """
        Get command to create openshift route
        """
        service = "varnish-varnish"
        if self._openshift_namespace == "wwp-test":
            service = "varnish-test-varnish"

        yaml_content = f"""
              apiVersion: v1
              kind: Route
              metadata:
                annotations:
                  haproxy.router.openshift.io/balance: roundrobin
                labels:
                  app: httpd-{self._openshift_env}
                name: {self._route_name}
              spec:
                host: {self._hostname}
                port:
                  targetPort: http
                tls:
                  insecureEdgeTerminationPolicy: Redirect
                  termination: edge
                to:
                  kind: Service
                  name: {service}
                  weight: 100
                wildcardPolicy: None
          """
        command = f"echo \"{yaml_content}\" | oc -n {self._openshift_namespace} create -f -"
        return command
