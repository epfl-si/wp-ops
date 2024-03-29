from ansible.plugins.action import ActionBase
from ansible.errors import AnsibleError, AnsibleActionFail
from ansible.module_utils import six
from ansible_collections.epfl_si.actions.plugins.module_utils.subactions import Subaction

import re
import os
import json

class WordPressActionModule(ActionBase):

    def run(self, tmp=None, task_vars=None):

        # We have to initialize this var to avoid any errors.
        # It will be initialized in child classes
        self.result = None

        self._task_vars = task_vars  # For the _get_ansible_var() method
        self._subaction = Subaction(self, task_vars)

        return super(WordPressActionModule, self).run(tmp, task_vars)

    def _query_wp_cli (self, args):
        """
        Run WP-CLI to query state.

        If you want to change the WordPress state, use _run_wp_cli_change() instead.

        :param args: WP-CLI command to execute
        """
        return self._subaction.query("command", dict(_raw_params=self._make_wp_cli_command(args)))

    def _run_wp_cli_change (self, args, pipe_input=None):
        """
        Run WP-CLI to effect a change.

        If you want to read the WordPress state, use _query_wp_cli() instead.

        :param args: WP-CLI command to execute
        :param skip-loading-wp: if you don't want to load all the WP
        """
        return self._subaction.change("command", dict(_raw_params=self._make_wp_cli_command(args),
                                                      stdin=pipe_input),
                                      update_result=self.result)

    def _get_wp_json (self, suffix):
        return json.loads(self._query_wp_cli(suffix)['stdout'])

    def _make_wp_cli_command(self, args):
        return '{} {}'.format(
            self._get_ansible_var("wp_cli_command"),
            args)

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

    @property
    def _inventory_hostname(self):
        return self._get_ansible_var("inventory_hostname")

    def _is_filename (self, from_piece):
        """
        Tells if a path is a filename/folder name or not.

        :param from_piece: string describing plugin source.
        """
        if re.match(r'^https:\/\/github\.com\/', from_piece):
            # _is_filename should be true for URLs of files and (by extension)
            # of directories that are to be “cherry-picked” (rather than
            # cloned) out of a fraction of a repository. On the other hand,
            # “other” things on GitHub (such as a whole repository, with or without a
            # specified branch, or a released .zip) should return false.
            # if it has a branch, it's a full repo with a tree in the url
            if self._task.args.get('branch'):
                return
            else:
                return re.search(r'/(tree|blob)/', from_piece)
        else:
            return (from_piece != "wordpress.org/plugins"
                    and not from_piece.endswith(".zip"))

    def _is_check_mode (self):
        return self._task_vars.get('ansible_check_mode', False)


class WordPressPluginOrThemeActionModule(WordPressActionModule):
    """Common superclass for the wordpress_plugin and wordpress_theme action modules."""
    # Has to be set in child classes with one of the following value:
    # plugin
    # mu-plugin
    # theme
    _type = None
    # Has to be set with element name in child class
    _name = None
    # Tells if the element has to be here without any negociation (like mu-plugins) or not
    _mandatory = None


    def _get_type(self):
        """
        Return element type or raise an exception if not initialized
        """
        if self._type is None:
            raise ValueError("Please initiliaze 'self._type' in subclass {}".format(type(self).__name__))

        return self._type

    def _get_name(self):
        """
        Return element name or raise an exception if not initialized
        """
        if self._name is None:
            raise ValueError("Please initiliaze 'self._name' in children class {}".format(type(self).__name__))

        return self._name


    def _is_mandatory(self):
        """
        Return if element is mandatory or raise an exception if not initialized
        """
        if self._mandatory is None:
            raise ValueError("Please initiliaze 'self._mandatory' in children class {}".format(type(self).__name__))

        return self._mandatory


    def _get_desired_state(self):
        """
        Returns array with installation state and activation state for a (mu-)plugin or a theme.
        We look into YAML given args (plugins.yml)
        """
        desired_state = self._task.args.get('state', 'absent')
        if isinstance(desired_state, six.string_types):
             desired_state = set([desired_state.strip()])
        elif isinstance(desired_state, list):
            desired_state = set(desired_state)
        else:
            raise TypeError("Unexpected value for `state`: {}".format(desired_state))

        if 'symlinked' in desired_state and 'installed' in desired_state:
            raise ValueError('{} {} cannot be both `symlinked` and `installed`'.format(self._get_type(), self._get_name()))

        installation_state = self._installation_state(desired_state)
        activation_state = self._activation_state(desired_state)

        if installation_state == 'absent' and activation_state == 'active' and not self._is_mandatory():
            raise ValueError('{} {} cannot be simultaneously absent and {}'.format(
                             self._get_type(), self._get_name(), activation_state))

        if activation_state == 'active' or self._is_mandatory():
            # Cannot activate (or make a mu-plugin) if not installed
            if not installation_state:
                installation_state = 'symlinked'
        if installation_state == 'absent':
            # Must (attempt to) deactivate prior to uninstalling
            if not activation_state:
                activation_state = "inactive"

        return (installation_state, activation_state)


    def _ensure_all_files_state (self, desired_state):
        """
        Checks if all files/folder for a plugin are in the desired states (present, absent, ...)

        :param desired_state: can be 'installed', 'symlinked', ...
        """
        froms = self._task.args.get('from')
        if isinstance(froms, six.string_types):
            froms = [froms]
        if not froms:
            froms = []

        basenames = [os.path.basename(f) for f in froms
                if self._is_filename(f)]
        if not basenames:
            basenames = [self._get_name()]

        # Going through each files/folder for plugin

        def query(task, args):
            return self._subaction.query(task, args)

        def change(task, args):
            return self._subaction.change(task, args, update_result=self.result)

        for basename in basenames:
            AssetFile(wp_dir=self._get_wp_dir(),
                      wp_subdir="wp-content/{}s".format(self._get_type()),
                      basename=basename).ensure_state(query, change, desired_state)


    def _do_activate_element(self):
        """
        Uses WP-CLI to activate plugin
        """
        return self._run_wp_cli_change(
            '{} activate {}'.format(self._get_type(), self._get_name()))


    def _activation_state(self, desired_state):
        """
        Returns plugin activation state based on desired state (active, inactive)

        :param desired_state: Plugin desired activation state
        """

        # Active by default
        if self._is_mandatory():
            return 'active'

        activation_state = desired_state.intersection(['active', 'inactive'])
        if len(activation_state) == 0:
            return None
        elif len(activation_state) == 1:
            return list(activation_state)[0]
        else:
            raise ValueError('{} {} cannot be simultaneously {}'.format(self._get_type(), self._get_name(), str(list(activation_state))))


    def _installation_state(self, desired_state):
        """
        Returns plugin installation state based on desired state (present, absent, symlinked)

        :param desired_state: Plugin desired installation state
        """
        installation_state = desired_state.intersection(['present', 'absent', 'symlinked', 'installed'])
        if len(installation_state) == 0:
            return None
        elif len(installation_state) == 1:
            return list(installation_state)[0]
        else:
            raise ValueError('{} {} cannot be simultaneously {}'.format(self._get_type(), self._get_name(), str(list(installation_state))))


    def _get_activation_state (self):
        """
        Returns plugin activation state
        """
        # To use 'wp plugin' for MU-Plugins
        wp_command = 'plugin' if self._get_type() == 'mu-plugin' else self._get_type()

        result = self._query_wp_cli('{} list --format=csv'.format(wp_command))

        if 'failed' in result: return

        for line in result["stdout"].splitlines()[1:]:
            fields = line.split(',')
            if len(fields) < 2: continue
            if fields[0] == self._get_name(): return fields[1]
        return 'inactive'


class AssetFile(object):
    def __init__(self, wp_dir, wp_subdir, basename):
        """
        Constructor

        :param wp_dir: The path of the WordPress site this AssetFile belongs to
        :param wp_subdir: The path this particular kind of AssetFile lives in, e.g. "wp_content/themes", "wp_content/plugins" or "wp_content/mu-plugins"
        :param basename: file/folder of a plugin or theme
        """
        self.wp_dir = wp_dir
        self.wp_subdir = wp_subdir
        self.basename = basename


    def _get_current_state (self, query):
        """
        Returns state of a given plugin file/folder.

        :param query: A function that takes the name and parameters of an Ansible task, to be used to query the current state of the file
        """
        path = self._abspath
        plugin_stat = query('stat', { 'path': path })
        if 'failed' in plugin_stat:
            raise AnsibleActionFail("Cannot stat() {} - Error: {}".format(path, plugin_stat))
        file_exists = ('stat' in plugin_stat and plugin_stat['stat']['exists'])
        if not file_exists:
            return 'absent'
        if not plugin_stat['stat']:
            return 'absent'
        elif plugin_stat['stat']['islnk']:
            if (plugin_stat['stat']['lnk_target'] ==
                self._get_symlink_target()):
                return 'symlinked'
            else:
                return 'symlink_damaged'
        else:
            return 'installed'


    def ensure_state (self, query, change, desired_state):
        """
        Check if a given (mu-)plugin file/folder is at the desired state

        :param query: A function that takes the name and parameters of an Ansible task, to be used to query the current state of the file
        :param change: A function that takes the name and parameters of an Ansible task, to be used to alter the state of the file (i.e. delete it or symlink it)
        :param desired_state: can be 'installed', 'symlinked', ...
        """
        current_state = self._get_current_state(query)
        if current_state == desired_state:
            return

        self._do_rimraf(change)

        if desired_state == 'installed':
            self._do_copy(change)

        else:
            self._do_symlink(change)


    def _do_symlink (self, change):
        """
        Creates a symlink for this file asset.

        :param change: A function that takes the name and parameters of an Ansible task, to be used to alter the state of the file (i.e. delete it or symlink it)
        """
        return change(
            'file',
            {'state': 'link',
            # Beware src / path inversion, as is customary with everything symlink:
             'src': self._get_symlink_target(),
             'path': self._abspath})


    def _do_rimraf (self, change):
        """
        Remove this file asset from disk.

        :param change: A function that takes the name and parameters of an Ansible task, to be used to alter the state of the file (i.e. delete it or symlink it)
        """
        return change(
            'file',
            {'state': 'absent',
             'path': self._abspath})


    def _do_copy (self, change):
        """
        Copy files out of /wp (via the symlink that is assumed to point to the correct WordPress version already).

        If caller wants to manage files using e.g. `wp plugin
        install` instead, it should do so before calling us, so
        that `current_state == desired_state` by the time we
        reach here.

        :param change: A function that takes the name and parameters of an Ansible task, to be used to alter the state of the file (i.e. delete it or symlink it)
        """
        return change('copy',
                      { 'remote_src': True,
                        'src': '%s/wp/%s/%s' % (self.wp_dir, self.wp_subdir,
                                                self.basename),
                        'dest': '%s/%s' % (self.wp_dir, self.wp_subdir)
                       })


    @property
    def _abspath (self):
        """
        Returns symlink source path
        """
        return self._make_element_path(self.wp_dir)


    def _get_symlink_target (self):
        """
        Returns a path that this asset should be symlinked to (if symlinking is desired)
        """
        return self._make_element_path('../../wp')


    def _make_element_path (self, prefix):
        """
        Generates path for this file asset, relative to `prefix`.

        :param prefix: The relative or absolute path that the returned path should start with.
        """
        return '{}/{}/{}'.format(prefix, self.wp_subdir, self.basename)
