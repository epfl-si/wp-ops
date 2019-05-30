#!/usr/bin/python
# -*- coding: utf-8 -*-

"""Run a script through Ansible Tower's awx-python, with Django loaded.

Django will be loaded before the script runs. The script may call
exit_json() or throw an AnsibleError, much like an Ansible task would.
Additionally, it may call the update_json_status() global function.

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
        self.json_status = {'changed': False}
        self.update_json_status_called = False
        self.exit_json_called = False

    def run(self):
        check_mode = self.module.check_mode
        if check_mode and not self.module.params.get('supports_check_mode'):
            return self.exit_json(skipped=True)

        vars = deepcopy(self.module.params.get('vars'))
        vars['check_mode'] = check_mode
        vars['AnsibleError'] = AnsibleError
        vars['exit_json'] = self.exit_json
        vars['update_json_status'] = self.update_json_status

        self.load_django()
        try:
            exec(self.module.params.get('script'), vars)
            if not self.exit_json_called:
                if self.update_json_status_called:
                    self.exit_json(**self.json_status)
                else:
                    # Conservative behavior for scripts that don't manage
                    # the status at all
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

    def update_json_status(self, **kwargs):
        self.update_json_status_called = True
        # TODO: This is too crude; we don't want to e.g. override
        # {'changed': True} with {'changed': False}
        self.json_status.update(**kwargs)


if __name__ == '__main__':
    AwxScriptTask().run()
