#!/usr/bin/python3

"""Install WordPress plugins and themes from various locations."""

import atexit
from collections import namedtuple
import getopt
import inspect
from io import BytesIO
import json
import os
import re
import requests
import shutil
from six import string_types
import subprocess
import sys
import tempfile
import yaml
from zipfile import ZipFile


def usage():
    print("""
Usage:

  install-plugins-and-themes.py auto [--exclude <plugin-name> ...]

    Install all plugins (and in the future, also mu-plugins and themes)
    into /wp. The list and addresses of plugins to install is determined
    from the current state of the source code (currently, by
    interpreting data/plugins/generic/config-lot1.yml out of branch
    `release2018` in https://github.com/epfl-idevelop/jahia2wp)

  install-plugins-and-themes.py <name> <URL>

    Install one plugin or theme into the current directory. <name> is
    the name of the subdirectory to create. <URL> can point to a ZIP
    file, a GitHub URL (possibly pointing to a particular branch and
    subdirectory), or it can be the string "web" to mean that the
    plug-in named <name> shall be downloaded from the WordPress plugin
    repository.

Options:

  --exclude <plugin-name>

    Exclude that plugin when in "auto" mode
""")


def progress(string):
    print("# {}".format(string))


def run_cmd(cmd, *args, **kwargs):
    if isinstance(cmd, string_types):
        cmd_text = cmd
    else:
        cmd_text = " ".join(cmd)
    if 'cwd' in kwargs:
        cmd_text = 'cd "{}"; {}'.format(kwargs['cwd'], cmd_text)
    progress(cmd_text)
    return subprocess.call(cmd, *args, **kwargs)


class class_or_instance_method(object):
    """From https://stackoverflow.com/a/55732871/435004"""

    def __init__(self, f):
        self.f = f

    def __get__(self, instance, owner):
        if instance is not None:
            wrt = instance
        else:
            wrt = owner

        def newfunc(*args, **kwargs):
            return self.f(wrt, *args, **kwargs)
        return newfunc


class Tempdir:
    """A temporary directory."""
    def __init__(self):
        self._dir = tempfile.mkdtemp(prefix="install-plugins-")
        atexit.register(self.clean)

    def __repr__(self):
        return self._dir

    def clean(self):
        progress('Deleting {}'.format(self._dir))
        shutil.rmtree(self._dir)


class GitHubCheckout:
    """A subdirectory found on GitHub, designated by its URL."""

    def __init__(self, url):
        """Class constructor.

        @param url The URL to `git clone` from. Shall start with
        `https://github.com`; may contain a branch (e.g.
        `https://github.com/foo/bar/tree/mybranch`) and a path to a
        subdirectory (e.g. `https://github.com/foo/bar/tree/mybranch/sub/dir`)
        """
        self.url = url
        self._parsed = self._parse(url)

    @classmethod
    def is_valid(cls, url):
        return bool(cls._parse(url))

    @classmethod
    def _parse(cls, url):
        matched_with_tree = re.match(
            'https://github.com/([^/]*)/([^/]*)/tree/([^/]*)(?:$|/(.*))', url)
        if matched_with_tree:
            return matched_with_tree
        else:
            return re.match(
                'https://github.com/([^/]*)/([^/]*)$', url)

    @property
    def github_namespace(self):
        return self._parsed.group(1)

    @property
    def github_project(self):
        return self._parsed.group(2)

    @property
    def branch(self):
        try:
            return self._parsed.group(3)
        except IndexError:
            return None

    @property
    def path_under_git_root(self):
        try:
            return self._parsed.group(4)
        except IndexError:
            return None

    @property
    def clone_url(self):
        return 'https://github.com/{}/{}'.format(
            self.github_namespace, self.github_project)

    def clone(self):
        if not hasattr(self, '_git_topdir'):
            tmp = Tempdir()
            run_cmd(["git", "clone", self.clone_url], cwd=str(tmp))
            self._git_topdir = os.path.join(str(tmp), self.github_project)
            if self.branch is not None:
                run_cmd(["git", "checkout", self.branch], cwd=self._git_topdir)
        return self  # For chaining

    @property
    def source_dir(self):
        if self.path_under_git_root is not None:
            return os.path.join(self._git_topdir, self.path_under_git_root)
        else:
            return self._git_topdir


class Plugin(namedtuple('Plugin', ['name', 'url'])):
    """A WordPress plug-in or theme."""
    def __new__(cls, name, url):
        if cls is Plugin:
            cls = cls._find_handler(url)

        that = tuple.__new__(cls, (name, url))
        that.__init__(name, url)
        return that

    @staticmethod
    def subclasses():
        return (ZipPlugin, GitHubPlugin, Jahia2wpSubdirectoryPlugin,
                WordpressOfficialPlugin)

    @classmethod
    def _find_handler(cls, url):
        for handler_class in cls.subclasses():
            if handler_class.handles(url):
                return handler_class
        raise Exception(
            "Don't know how to handle plug-in URL: {}".format(url))

    def _copytree_install(self, from_path, to_path):
        to_path = os.path.join(to_path, self.name)
        progress('Copying {} to {}'.format(from_path, to_path))
        shutil.copytree(from_path, to_path)


class ZipPlugin(Plugin):
    """A WordPress plug-in in Zip form.

    Also handled here: the case where `url` is a relative path, in
    which case it is interpreted as the path of a .zip file in the
    jahia2wp source tree (using @link Jahia2p.data_plugins_path_relative)
    """
    @classmethod
    def handles(cls, url):
        return url.endswith(".zip")

    def install(self, target_dir):
        """Unzip into a subdirectory `target_dir` named `self.name`."""
        if self.url.startswith("http"):
            zip = ZipFile(BytesIO(requests.get(self.url).content))
        else:
            zip = ZipFile(Jahia2wp.data_plugins_path_relative(self.url))
        progress("Unzipping {}".format(self.url))
        for member in zip.namelist():
            zipinfo = zip.getinfo(member)
            if zipinfo.filename[-1] == '/':
                continue

            targetpathelts = os.path.normpath(zipinfo.filename).split('/')
            targetpathelts[0] = self.name

            targetpath = os.path.join(target_dir, *targetpathelts)

            upperdirs = os.path.dirname(targetpath)
            if upperdirs and not os.path.exists(upperdirs):
                os.makedirs(upperdirs)

            with zip.open(zipinfo) as source, open(targetpath, "wb") as target:
                shutil.copyfileobj(source, target)


class GitHubPlugin(Plugin):
    """A plug-in to clone from GitHub."""
    @classmethod
    def handles(cls, url):
        return GitHubCheckout.is_valid(url)

    def __init__(self, name, url):
        self._git = GitHubCheckout(url)

    def install(self, target_dir):
        self._copytree_install(self._git.clone().source_dir, target_dir)


class WordpressOfficialPlugin(Plugin):
    """A plug-in to download from the official plug-in repository."""
    @classmethod
    def handles(cls, url):
        return url == 'web'

    @property
    def api_struct(self):
        api_json = requests.get(
            "https://api.wordpress.org/plugins/info/1.0/{}.json".format(self.name)
        ).content

        if "Plugin not found" in str(api_json):
            raise Exception("WordPress plugin not found: {}".format(self.name))
        return json.loads(api_json)

    def install(self, target_dir):
        ZipPlugin(self.name, self.api_struct['download_link']).install(target_dir)


class Themes:
    """The set of themes offered as part of the EPFL WordPress project."""
    @classmethod
    def all(cls):
        return (
            Plugin('wp-theme-2018',
                   'https://github.com/epfl-idevelop/wp-theme-2018/tree/master/wp-theme-2018'),
            Plugin('wp-theme-light',
                   'https://github.com/epfl-idevelop/wp-theme-2018/tree/master/wp-theme-light'),
            Plugin('epfl-blank',
                   'https://github.com/epfl-idevelop/jahia2wp/tree/release/data/wp/wp-content/themes/epfl-blank'),
            Plugin('epfl-master',
                   'https://github.com/epfl-idevelop/jahia2wp/tree/release/data/wp/wp-content/themes/epfl-master')
        )


def MuPlugins():
    return Plugin(
        'mu-plugins',
        'https://github.com/epfl-idevelop/jahia2wp/tree/release2018/data/wp/wp-content/mu-plugins')


class Jahia2wpSubdirectoryPlugin(Plugin):
    """A plug-in whose source code lives in the jahia2wp source tree."""
    @classmethod
    def handles(cls, url):
        return bool(cls._parse(url))

    @classmethod
    def _parse(cls, url):
        return re.match("[.][.]/wp/wp-content/plugins/([^/]*)", url)

    @property
    def plugin_dir(self):
        return Jahia2wp.wp_content_plugins_path_relative(
            self._parse(self.url).group(1))

    def install(self, target_dir):
        self._copytree_install(self.plugin_dir, target_dir)


class Jahia2wp:
    """Models the jahia2wp source tree.

    For historical reasons, this Git repository contains code that
    deals with some "ops" aspects such as creating sites, mixed with
    WordPress plug-ins, mu-plugins and more.
    """

    _GIT_URL = 'https://github.com/epfl-idevelop/jahia2wp/tree/release2018'
    _DATA_PLUGINS_DIR = 'data/plugins'
    _CONFIG_LOT1_YML_PATH = 'generic/config-lot1.yml'
    _WP_PLUGINS_DIR = 'data/wp/wp-content/plugins'

    @classmethod
    def singleton(cls):
        if not hasattr(cls, "_singleton"):
            cls._singleton = cls()
        return cls._singleton

    def __init__(self):
        self._git = GitHubCheckout(self._GIT_URL)
        self._git.clone()

    @property
    def path(self):
        return self._git.source_dir

    @class_or_instance_method
    def path_relative(self, *path_fragments):
        if inspect.isclass(self):
            self = Jahia2wp.singleton()
        return os.path.join(self.path, *path_fragments)

    @class_or_instance_method
    def data_plugins_path_relative(self, *path_fragments):
        return self.path_relative(self._DATA_PLUGINS_DIR, *path_fragments)

    @class_or_instance_method
    def wp_content_plugins_path_relative(self, *path_fragments):
        return self.path_relative(self._WP_PLUGINS_DIR, *path_fragments)

    @property
    def config_lot1_path(self):
        return self.data_plugins_path_relative(self._CONFIG_LOT1_YML_PATH)

    def plugins(self):
        """Yield all the plug-ins to be installed according to the "ops" metadata."""

        lot1_struct = Jahia2wpLegacyYAMLLoader.load(self.config_lot1_path)
        for plugin_struct in lot1_struct['plugins']:
            name = plugin_struct['name']
            try:
                url = plugin_struct['config']['src']
            except KeyError:
                progress("Skipping {}".format(name))
                continue
            progress("{} -> {}".format(name, url))
            yield Plugin(name, url)


class Jahia2wpLegacyYAMLLoader(yaml.Loader):
    """Like yaml.Loader, but with !include and !from_csv.

    The latter is mocked out since we only care about the plugin list.
    """
    def __init__(self, *args, **kwargs):
        super(Jahia2wpLegacyYAMLLoader, self).__init__(*args, **kwargs)
        self.add_constructor("!include", self.__yaml_include)
        self.add_constructor("!from_csv", self.__yaml_from_csv)

    def __yaml_include(self, loader, node):
        """Make "!include" work in YAML files."""
        local_file = os.path.join(os.path.dirname(loader.stream.name),
                                  node.value)

        # if file to include exists with given value
        if os.path.exists(node.value):
            include_file = node.value
        # if file exists with relative path to current YAML file
        elif os.path.exists(local_file):
            include_file = local_file
        else:
            error_message = "YAML include in '{}' - file to include doesn't exist: {}".format(
                loader.stream.name, node.value)
            raise Exception(error_message)

        with open(include_file) as inputfile:
            # Yow, recursive !include's
            return Jahia2wpLegacyYAMLLoader.load(inputfile)

    def __yaml_from_csv(self, *unused_args, **unused_kwargs):
        # TODO: Right now we only care about plugin metadata insofar
        # as it helps us make a decision related to installing it into
        # the image or not. The bits formerly included from CSV
        # currently have no bearing on that; furthermore we will
        # probably want to refactor these parts of the YAML setup to
        # be more Ansible-like.
        return "UNUSED"

    @classmethod
    def load(cls, filename_or_stream):
        """Convenience shortcut, for when you don't want to learn the PyYAML API."""
        if not hasattr(filename_or_stream, "read"):
            filename_or_stream = open(filename_or_stream)
        return cls(filename_or_stream).get_single_data()


class Flags:
    """Command-line parser"""
    def __init__(self, argv=sys.argv[:]):
        if argv[0].endswith('.py'):
            argv.pop(0)

        self.auto = argv[0] == 'auto'
        if self.auto:
            try:
                opts, args = getopt.getopt(argv[1:], "e:v", ["exclude="])
            except getopt.GetoptError:
                usage()
                sys.exit(1)
            self.exclude = set(a for o, a in opts if o in ("-e", "--exclude"))
        else:
            self.name = argv[0]
            self.path = argv[1]


WP_INSTALL_DIR = '/wp/wp-content'
WP_PLUGINS_INSTALL_DIR = os.path.join(WP_INSTALL_DIR, 'plugins')
WP_THEMES_INSTALL_DIR = os.path.join(WP_INSTALL_DIR, 'themes')


if __name__ == '__main__':
    flags = Flags()

    if flags.auto:
        MuPlugins().install(WP_INSTALL_DIR)
        for plugin in Jahia2wp.singleton().plugins():
            if plugin.name not in flags.exclude:
                plugin.install(WP_PLUGINS_INSTALL_DIR)
        for theme in Themes.all():
            theme.install(WP_THEMES_INSTALL_DIR)
    else:
        name = sys.argv[0]
        url = sys.argv[1]
        Plugin(name, url).install('.')
