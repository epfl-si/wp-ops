# -*- coding: utf-8 -*-

from ansible.plugins.action import ActionBase
from ansible.errors import AnsibleActionFail
from ansible.module_utils import six

class ActionModule(ActionBase):
    def run (self, tmp=None, task_vars=None):
        self.result = super(ActionModule, self).run(tmp, task_vars)
        self._tmp = tmp
        self._task_vars = task_vars

        args = self._task.args
        desired_state = args.get('state', 'absent')
        if isinstance(desired_state, six.string_types):
            desired_state = desired_state.strip()

        name = args.get('name')

        current_state = self._get_plugin_state(name)
        if (desired_state == current_state):
            pass
        elif desired_state == 'absent':
            self.result.update(self._do_uninstall_plugin(name))
        elif ('must-use' in desired_state):
            pass  # TODO later - The `wp plugin install` command cannot help us here
        elif 'symlinked' in desired_state:
            if current_state != 'absent' and 'symlinked' not in current_state:
                self.result.update(self._do_rimraf_plugin(name))
                if 'failed' in self.result: return result

            self.result.update(self._do_symlink_plugin(name))
            if 'failed' in self.result: return result
            
            if ('failed' not in self.result) and (desired_state != 'symlinked-inactive'):
                self.result.update(self._do_activate_plugin(name))
                
        else:
            raise AnsibleActionFail('Cannot transition plugin %s from state %s to %s' %
                                    (name, current_state, desired_state))

        return self.result

    def _get_plugin_state (self, name):
        plugin_stat = self._run_action(
            'stat',
            {
             'path': self._get_plugin_path(name)
             })
        if 'failed' in plugin_stat: return plugin_stat

        if not ('stat' in plugin_stat and plugin_stat['stat']['exists']):
            return 'absent'
        elif plugin_stat['stat']['islnk']:
            if self._is_plugin_active(name):
                return 'symlinked'
            else:
                return 'symlinked-inactive'
        else:
            if self._is_plugin_active(name):
                return 'active'
            else:
                return 'installed'

    def _do_uninstall_plugin (self, name):
        result = self._run_wp_cli_action('plugin deactivate %s' % name)
        if 'failed' not in result:
            result.update(self._do_rimraf_plugin(name))
        return result

    def _do_symlink_plugin (self, name):
        return self._run_action('file', {
            'state': 'link',
            'src': '../../wp/wp-content/plugins/%s' % name,
            'path': '%s/wp-content/plugins/%s' % (self._get_wp_dir(), name),
            })

    def _do_activate_plugin (self, name):
        return self._run_wp_cli_action('plugin activate %s' % name)

    def _do_rimraf_plugin (self, name):
        return self._run_action(
            'file',
            {'state': 'absent',
             'path': self._get_plugin_path(name)}) 

    def _run_wp_cli_action (self, args):
        return self._run_shell_action(
            '%s %s' % (self._get_ansible_var('wp_cli_command'), args))

    def _run_shell_action (self, cmd):
        return self._run_action('command', { '_raw_params': cmd, '_uses_shell': True })

    def _run_action (self, action_name, args):
        # https://www.ansible.com/blog/how-to-extend-ansible-through-plugins
        # at § “Action Plugins”
        return self._execute_module(module_name=action_name,
                                    module_args=args, tmp=self._tmp, task_vars=self._task_vars)

    def _get_wp_dir (self):
        return self._get_ansible_var('wp_dir')

    def _get_plugin_path (self, name):
        return '%s/wp-content/plugins/%s' % (self._get_wp_dir(), name)

    def _is_plugin_active (self, name):
        result = self._run_wp_cli_action('plugin status %s' % name)
        return (result and 'Status: Active' in result.get('stdout', ''))

    def _get_ansible_var (self, name):
        unexpanded = self._task_vars.get(name, None)
        if unexpanded is None:
            return None
        else:
            return self._templar.template(unexpanded)


