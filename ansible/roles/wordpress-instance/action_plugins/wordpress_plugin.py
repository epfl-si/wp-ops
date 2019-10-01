# -*- coding: utf-8 -*-

# There is a name clash with a module in Ansible named "copy":
deepcopy = __import__('copy').deepcopy
import re

from ansible.plugins.action import ActionBase
from ansible.errors import AnsibleActionFail
from ansible.module_utils import six

class ActionModule(ActionBase):
    def run (self, tmp=None, task_vars=None):
        self.result = super(ActionModule, self).run(tmp, task_vars)
        self._tmp = tmp
        self._task_vars = task_vars

        args = self._task.args

        name = args.get('name')

        current_state = self._get_current_state(name)
        desired_state = self._get_desired_state(name, args)
        to_do = desired_state - current_state
        to_undo = current_state - desired_state
        cares_about_installation_state = bool(self._desired_installation_state(desired_state))
        cares_about_activation_state = bool(self._desired_activation_state(desired_state))
        must_install_implicitly = ('symlinked' not in current_state and
                                   'installed' not in current_state and
                                   not cares_about_installation_state and
                                   cares_about_activation_state)

        if 'must-use' in desired_state:
            # TODO — UNIMPLEMENTED Some must-use plug-ins have two
            # files to symlink, and the structure of the code doesn't
            # allow for that yet.
            return self.result

        if not (to_do or to_undo):
            return self.result

        if 'installed' in to_do:
            raise NotImplementedError('Installing "regular" (non-symlinked) plugin %s '
                                      'not supported (yet)' % name)


        if cares_about_activation_state and 'active' in to_undo:
            self._update_result(self._do_deactivate_plugin(name))
            if 'failed' in self.result: return self.result

        if  cares_about_installation_state and (
                'symlinked' in to_undo or 'installed' in to_undo):
            self._update_result(self._do_rimraf_plugin(name))
            if 'failed' in self.result: return self.result

        if ( (cares_about_installation_state and 'symlinked' in to_do)
             or must_install_implicitly):
            self._update_result(self._do_symlink_plugin(name, 'must-use' in desired_state))
            if 'failed' in self.result: return self.result

        if cares_about_activation_state and 'active' in to_do:
            self._update_result(self._do_activate_plugin(name))
            if 'failed' in self.result: return self.result

        return self.result

    def _get_current_state (self, name):
        path = self._get_plugin_path(name)
        plugin_stat = self._run_action('stat', { 'path': path })
        if 'failed' in plugin_stat:
            raise AnsibleActionFail("Cannot stat() %s" % path)

        if not ('stat' in plugin_stat and plugin_stat['stat']['exists']):
            return set(['absent'])
        elif plugin_stat['stat']['islnk']:
            return set(['symlinked', self._get_plugin_activation_state(name)])
        else:
            return set(['installed', self._get_plugin_activation_state(name)])

    def _get_desired_state(self, name, args):
        desired_state = args.get('state', 'absent')
        if isinstance(desired_state, six.string_types):
             desired_state = set([desired_state.strip()])
        elif isinstance(desired_state, list):
            desired_state = set(desired_state)
        else:
            raise TypeError("Unexpected value for `state`: %s" % state)

        if 'symlinked' in desired_state and 'installed' in desired_state:
            raise ValueError('Plug-in %s cannot be both `symlinked` and `installed`' % name)

        installation_state = self._desired_installation_state(desired_state)
        activation_state = self._desired_activation_state(desired_state)

        if 'absent' == installation_state and activation_state:
            raise ValueError('Plug-in %s cannot be simultaneously absent and %s' %
                             (name, activation_state))

        return desired_state

    def _do_uninstall_plugin (self, name):
        result = self._run_wp_cli_action('plugin deactivate %s' % name)
        if 'failed' not in result:
            result.update(self._do_rimraf_plugin(name))
        return result

    def _desired_installation_state(self, desired_state):
        installation_state = desired_state.intersection(['present', 'absent', 'symlinked'])
        if len(installation_state) == 0:
            return None
        elif len(installation_state) == 1:
            return list(installation_state)[0]
        else:
            raise ValueError('Plug-in %s cannot be simultaneously %s' % (
                name, list(installation_state)))

    def _desired_activation_state(self, desired_state):
        activation_state = desired_state.intersection(['active', 'inactive', 'must-use'])
        if len(activation_state) == 0:
            return None
        elif len(activation_state) == 1:
            return list(activation_state)[0]
        else:
            raise ValueError('Plug-in %s cannot be simultaneously %s' %
                             (name, list(activation_state)))

    def _do_symlink_plugin (self, name, is_mu):
        return self._run_action('file', {
            'state': 'link',
            'src': self._make_plugin_path('../../wp', name, is_mu),
            'path': self._make_plugin_path(self._get_wp_dir(), name, is_mu),
            })

    def _do_activate_plugin (self, name):
        return self._run_wp_cli_action('plugin activate %s' % name)

    def _do_deactivate_plugin (self, name):
        return self._run_wp_cli_action('plugin deactivate %s' % name)

    def _do_rimraf_plugin (self, name):
        for path in (self._get_plugin_path(name),
                     self._get_muplugin_path(name)):
            if 'failed' in self.result: return self.result
            self._run_action(
                'file',
                {'state': 'absent',
                 'path': path}) 
        return self.result

    def _run_wp_cli_action (self, args):
        return self._run_shell_action(
            '%s %s' % (self._get_ansible_var('wp_cli_command'), args))

    def _run_shell_action (self, cmd):
        return self._run_action('command', { '_raw_params': cmd, '_uses_shell': True })

    def _run_action (self, action_name, args):
        # https://www.ansible.com/blog/how-to-extend-ansible-through-plugins
        # at § “Action Plugins”
        result = self._execute_module(module_name=action_name,
                                      module_args=args, tmp=self._tmp,
                                      task_vars=self._task_vars)
        self._update_result(result)
        return self.result

    def _get_wp_dir (self):
        return self._get_ansible_var('wp_dir')

    def _get_plugin_path (self, name):
        return self._make_plugin_path(self._get_wp_dir(), name, False)

    def _get_muplugin_path (self, name):
        return self._make_plugin_path(self._get_wp_dir(), name, True)

    def _make_plugin_path(self, prefix, name, is_mu):
        return '%s/wp-content/%splugins/%s' % (
            prefix,
            'mu-' if is_mu else '',
            name)

    def _get_plugin_activation_state (self, name):
        oldresult = deepcopy(self.result)
        result = self._run_wp_cli_action('plugin list --format=csv')
        if 'failed' in self.result: return self.result

        self.result = oldresult  # We don't want "changed" to pollute the state

        for line in result["stdout"].splitlines()[1:]:
            fields = line.split(',')
            if len(fields) < 2: continue
            if fields[0] == name: return fields[1]
        return 'inactive'

    def _get_ansible_var (self, name):
        unexpanded = self._task_vars.get(name, None)
        if unexpanded is None:
            return None
        else:
            return self._templar.template(unexpanded)

    def _update_result (self, result):
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
