#!/usr/bin/python
# -*- coding: utf-8 -*-

"""Run a script through Ansible Tower's awx-python, with Django loaded.

The script may call exit_json() or throw an AnsibleError, much like an
Ansible task would. Additionally, Django will be loaded before the
script runs.

See AwxScriptTask.module_spec for supported task parameters.
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
            vars=dict(type='dict'),
            supports_check_mode=dict(default=False, type='bool')
        ),
        supports_check_mode=True  # We make do, even if the script doesn't
    )

    def __init__(self):
        self.module = AnsibleModule(**self.module_spec)
        self.exit_json_called = False

    def run(self):
        check_mode = self.module.check_mode
        if check_mode and not self.module.params.get('supports_check_mode'):
            return self.exit_json(skipped=True)

        vars = deepcopy(self.module.params.get('vars'))
        vars['exit_json'] = self.exit_json
        vars['AnsibleError'] = AnsibleError
        vars['check_mode'] = check_mode

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
