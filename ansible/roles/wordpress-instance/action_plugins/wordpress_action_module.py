
# There is a name clash with a module in Ansible named "copy":
deepcopy = __import__('copy').deepcopy

from ansible.plugins.action import ActionBase
from ansible.errors import AnsibleActionFail
from ansible.module_utils import six


class WordPressActionModule(ActionBase):

    def run(self, tmp=None, task_vars=None):

        self._tmp = tmp
        self._task_vars = task_vars

        return super(WordPressActionModule, self).run(tmp, task_vars)


    def _run_wp_cli_action (self, args):
        """
        Executes a given WP-CLI command

        :param args: WP-CLI command to execute
        """
        return self._run_shell_action(
            '%s %s' % (self._get_ansible_var('wp_cli_command'), args))


    def _run_shell_action (self, cmd):
        """
        Executes a Shell command

        :param cmd: Command to execute.
        """
        with open('/tmp/ansible/log.lulu', 'a') as f:
            f.write("{}\n".format(cmd))
        return self._run_action('command', { '_raw_params': cmd, '_uses_shell': True })


    def _run_action (self, action_name, args):
        """
        Executes an action, using an Ansible module.

        :param action_name: Ansible module name to use
        :param args: dict with arguments to give to module
        """
        # https://www.ansible.com/blog/how-to-extend-ansible-through-plugins at "Action Plugins"
        result = self._execute_module(module_name=action_name,
                                      module_args=args, tmp=self._tmp,
                                      task_vars=self._task_vars)
        self._update_result(result)
        return self.result


    def _get_wp_dir (self):
        """
        Returns directory in which WordPress is installed
        """
        return self._get_ansible_var('wp_dir')


    def _get_ansible_var (self, name):
        """
        Returns Ansible var value

        :param name: Var name
        """
        unexpanded = self._task_vars.get(name, None)
        if unexpanded is None:
            return None
        else:
            return self._templar.template(unexpanded)


    def _update_result (self, result):
        """
        Updates result dict

        :param result: dict to update with
        """
        oldresult = deepcopy(self.result)
        self.result.update(result)

        def _keep_flag(flag_name):
            if (flag_name in oldresult and
                oldresult[flag_name] and
                flag_name in self.result and
                not result[flag_name]
            ):
                self.result[flag_name] = oldresult[flag_name]

        _keep_flag('changed')

        return self.result
