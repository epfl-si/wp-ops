#!/usr/bin/python
# -*- coding: utf-8 -*-

"""Run a script through Ansible Tower's awx-python, with Django loaded.

The script may call exit_json() or throw an AnsibleError, much like an
Ansible task would. Additionally, Django will be loaded before the
script runs.
"""

from ansible.module_utils.basic import AnsibleModule
try:
    from ansible.errors import AnsibleError
except ImportError:
    AnsibleError = Exception

deepcopy = __import__('copy').deepcopy


class AwxScriptTask(object):

    module_spec = dict(
        argument_spec=dict(
            script=dict(type='str'),
            vars=dict(type='dict')
        )
    )

    def __init__(self):
        self.module = AnsibleModule(**self.module_spec)
        self.exit_json_called = False

    def run(self):
        vars = deepcopy(self.module.params.get('vars'))
        vars['exit_json'] = self.exit_json
        vars['AnsibleError'] = AnsibleError

        self.load_django()
        try:
            exec(self.module.params.get('script'), vars)
            if not self.exit_json_called:
                self.exit_json(changed=True)
        except Exception as exn:
            self.exit_json(
                failed=True,
                msg=repr(exn),
                exception_class=exn.__class__.__name__)

    def load_django(self):
        # Reverse-engineered from manage() in
        # /var/lib/awx/venv/awx/lib/python3.6/site-packages/awx/__init__.py
        import awx
        import django
        awx.prepare_env()
        django.setup()

    def exit_json(self, *args, **kwargs):
        self.exit_json_called = True
        return self.module.exit_json(*args, **kwargs)


if __name__ == '__main__':
    AwxScriptTask().run()
