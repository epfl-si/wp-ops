from ansible.plugins.action import ActionBase


class ActionModule(ActionBase):
    def run(self, tmp=None, task_vars=None):
        return super(ActionModule, self).run(tmp, task_vars)
