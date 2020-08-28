# -*- coding: utf-8 -*-

import sys
import os.path
import subprocess
from route_helper import check_route_exist, getRouteName

# To be able to import wordpress_action_module
sys.path.append(os.path.dirname(__file__))

from ansible.module_utils import six
from wordpress_action_module import WordPressActionModule

class ActionModule(WordPressActionModule):

    def run (self, tmp=None, task_vars=None):
        self.result = super(ActionModule, self).run(tmp, task_vars)
        self._route_name = getRouteName(
            self._task.args.get('site_url'), 
            self._task.args.get('openshift_env')
        )
        self._openshift_namespace = self._task.args.get('openshift_namespace')

        if check_route_exist(self._openshift_namespace, self._route_name):
            subprocess.check_output(
                self._get_delete_route_command(),
                shell=True, encoding='utf-8')
            self.result['changed'] = True
        
        return self.result

    def _get_delete_route_command(self):
        """
        Get command to create openshift route
        """
        return f"oc -n {self._openshift_namespace} delete route {self._route_name}"
