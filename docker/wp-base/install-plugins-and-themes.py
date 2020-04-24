#!/usr/bin/env python3

"""Install WordPress plugins and themes from various locations."""

import atexit
import getopt
import io
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

AUTO_MANIFEST_URL = 'https://raw.githubusercontent.com/epfl-si/wp-ops/master/ansible/roles/wordpress-instance/tasks/plugins.yml'

def usage():
    print("""
Usage:

  install-plugins-and-themes.py auto [options ...]

    Install all plugins, mu-plugins and themes into the WordPress
    instance rooted at the current directory. The list and addresses
    of plugins to install is determined from the Ansible
    configuration.

    Options:

      --exclude <plugin-name>    Self-explanatory. Used to exclude proprietary
                                 plugins from Travis builds

      --manifest-url             The URL to obtain the plugin manifest from;
                                 default is %s

  install-plugins-and-themes.py <name> <URL>

    Install one plugin or theme into the current directory. <name> is
    the name of the subdirectory to create. <URL> can point to a ZIP
    file, a GitHub URL (possibly pointing to a particular branch and
    subdirectory), or it can be the string "wordpress.org/plugins",
    meaning that the plug-in named <name> shall be downloaded
    from the WordPress plugin repository.

Options:

  --exclude <plugin-name>

    Exclude that plugin when in "auto" mode
""" % AUTO_MANIFEST_URL)


def progress(string):
    print("# {}".format(string), file=sys.stderr)
    sys.stderr.flush()


def run_cmd(cmd, *args, **kwargs):
    if isinstance(cmd, string_types):
        cmd_text = cmd
    else:
        cmd_text = " ".join(cmd)
    if 'cwd' in kwargs:
        cmd_text = 'cd "{}"; {}'.format(kwargs['cwd'], cmd_text)
    progress(cmd_text)
    return subprocess.call(cmd, *args, **kwargs)


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
        assert self._parsed

    @classmethod
    def is_valid(cls, url):
        return bool(cls._parse(url))

    @classmethod
    def _parse(cls, url):
        for parse_re in (
                'https://github.com/([^/]*)/([^/]*)/(?:tree|blob)/((?:(?:feature|bugfix)/)?[^/]+)(?:$|/(.*))',
                'https://github.com/([^/]*)/([^/]*)$'):
            matched = re.match(parse_re, url)
            if matched:
                return matched

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

    _clone_cache = {}

    def clone(self):
        if not hasattr(self, '_git_topdir'):
            if (self.clone_url, self.branch) in self._clone_cache:
                self._git_topdir = self._clone_cache[(self.clone_url, self.branch)]
            else:
                tmp = Tempdir()
                progress("Cloning {}".format(self.clone_url))
                run_cmd(["git", "clone", self.clone_url], cwd=str(tmp))
                self._git_topdir = os.path.join(str(tmp), self.github_project)
                if self.branch is not None:
                    run_cmd(["git", "checkout", self.branch], cwd=self._git_topdir)
                self._clone_cache[(self.clone_url, self.branch)] = self._git_topdir

        return self  # For chaining

    @property
    def source_path(self):
        if self.path_under_git_root is not None:
            return os.path.join(self._git_topdir, self.path_under_git_root)
        else:
            return self._git_topdir


class Plugin(object):
    """A WordPress plug-in or theme."""

    def __init__(self, name, urls, **unused_kwargs):
        self.name = name
        self.urls = urls

    def __new__(cls, name, urls):
        if cls is Plugin:
            cls = cls._find_handler(urls[0])

        that = object.__new__(cls)
        that.__init__(name, urls)
        return that

    @staticmethod
    def subclasses():
        return (ZipPlugin, GitHubPlugin, WordpressOfficialPlugin)

    @classmethod
    def _find_handler(cls, url):
        for handler_class in cls.subclasses():
            if handler_class.handles(url):
                return handler_class
        raise Exception(
            "Don't know how to handle plug-in URL: {}".format(url))

    def _copytree_install(self, from_path, to_path, rename_dir=None):
        if os.path.isdir(from_path):
            if not rename_dir:
                rename_dir = os.path.basename(from_path)
            to_path = os.path.join(to_path, rename_dir)
            progress('Copying {} directory to {}'.format(from_path, to_path))
            shutil.copytree(from_path, to_path)
        else:
            progress('Copying {} file to {}'.format(from_path, to_path))
            shutil.copy(from_path, to_path)


class ZipPlugin(Plugin):
    """A WordPress plug-in in Zip form."""
    @classmethod
    def handles(cls, url):
        return url.endswith(".zip")

    def __init__(self, name, urls):
        super(ZipPlugin, self).__init__(name, urls)
        assert len(self.urls) == 1
        self.url = self.urls[0]
        assert self.url.startswith("http")

    def install(self, target_dir, rename_like_self=True):
        """Unzip into `target_dir`.

        Keyword arguments:
        rename_like_self -- Ignored - We always unzip to a subdirectory named
                            `self.name`
        """
        zip = ZipFile(io.BytesIO(requests.get(self.url).content))

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

    def __init__(self, name, urls):
        super(GitHubPlugin, self).__init__(name, urls)
        self._gits = [GitHubCheckout(url) for url in self.urls]

    def install(self, target_dir, rename_like_self=True):
        """Install by copying into `target_dir`.

        Keyword arguments:
        rename_like_self -- if set, rename the top-level directory to `self.name`.
                            (Ignored if the plug-in consists of a single file)
        """
        for git in self._gits:
            self._copytree_install(git.clone().source_path, target_dir,
                                   rename_dir=self.name if rename_like_self else None)


class WordpressOfficialPlugin(Plugin):
    """A plug-in to download from the official plug-in repository."""
    @classmethod
    def handles(cls, url):
        return url == 'wordpress.org/plugins'

    @property
    def api_struct(self):
        api_json = requests.get(
            "https://api.wordpress.org/plugins/info/1.0/{}.json".format(self.name)
        ).content

        if "Plugin not found" in str(api_json):
            raise Exception("WordPress plugin not found: {}".format(self.name))
        return json.loads(api_json)

    def install(self, target_dir):
        ZipPlugin(self.name, [self.api_struct['download_link']]).install(target_dir)


class Themes:
    """The set of themes offered as part of the EPFL WordPress project."""
    @classmethod
    def all(cls):
        return (
            Plugin('wp-theme-2018',
                   ['https://github.com/epfl-si/wp-theme-2018/tree/master/wp-theme-2018']),
            Plugin('wp-theme-light',
                   ['https://github.com/epfl-si/wp-theme-2018/tree/master/wp-theme-light']),
            Plugin('epfl-blank',
                   ['https://github.com/epfl-si/jahia2wp/tree/release/data/wp/wp-content/themes/epfl-blank']),
            Plugin('epfl-master',
                   ['https://github.com/epfl-si/jahia2wp/tree/release/data/wp/wp-content/themes/epfl-master'])
        )


class WpOpsPlugins:
    """Models the plugins enumerated in the "wp-ops" Ansible configuration."""

    def __init__(self, manifest_url=None):
        if manifest_url is None:
            manifest_url = AUTO_MANIFEST_URL

        progress("Obtaining plug-in manifest from {}".format(manifest_url))
        req = requests.get(manifest_url)
        if req.status_code != 200:
            raise Exception('requests.get("{}") yielded status {}'.format(
                manifest_url, req.status_code))
        self.plugins_yaml = req.content

    def _plugins_and_is_mu(self):
        for thing in yaml.load(self.plugins_yaml):
            try:
                if 'wordpress_plugin' not in thing:
                    continue
            except Exception as e:
                import pprint
                raise Exception(pprint.pformat(thing))
            options = thing['wordpress_plugin']

            # Defining if is MU-Plugin or not
            is_mu = False if 'is_mu' not in options else options['is_mu']

            # For unwanted plugins, the ones who are present but have to be uninstalled, ... ugly ducklings !
            # those ones have 'absent' for 'state' but this field is not used, it is only the missing 'from' which
            # prevent plugin from being present in image.
            if 'from' not in options:
                continue

            name = options['name']
            urls = options['from']
            if isinstance(urls, string_types):
                urls = [urls]


            yield (Plugin(name, urls), is_mu)

    def plugins(self):
        """Yield all the plug-ins to be installed according to the "ops" metadata."""
        for p, is_mu in self._plugins_and_is_mu():
            if not is_mu:
                yield p

    def must_use_plugins(self):
        """Yield all the must-use plug-ins to be installed according to the "ops" metadata."""
        for p, is_mu in self._plugins_and_is_mu():
            if is_mu:
                yield p


class Flags:
    """Command-line parser"""
    def __init__(self, argv=sys.argv[:]):
        if argv[0].endswith('.py'):
            argv.pop(0)

        self.auto = argv[0] == 'auto'
        if self.auto:
            try:
                opts, args = getopt.getopt(argv[1:], "e:v", ["exclude=", "manifest-url="])
            except getopt.GetoptError:
                usage()
                sys.exit(1)
            self.exclude = set(a for o, a in opts if o in ("-e", "--exclude"))
            self.manifest_url = None
            for o, a in opts:
                if o == "--manifest-url":
                    self.manifest_url = a
        else:
            self.name = argv[0]
            self.path = argv[1]


WP_INSTALL_DIR = './wp-content'
WP_PLUGINS_INSTALL_DIR = os.path.join(WP_INSTALL_DIR, 'plugins')
WP_MU_PLUGINS_INSTALL_DIR = os.path.join(WP_INSTALL_DIR, 'mu-plugins')
WP_THEMES_INSTALL_DIR = os.path.join(WP_INSTALL_DIR, 'themes')


if __name__ == '__main__':
    flags = Flags()

    if flags.auto:
        manifest = WpOpsPlugins(flags.manifest_url)
        for d in (WP_PLUGINS_INSTALL_DIR, WP_MU_PLUGINS_INSTALL_DIR):
            if not os.path.isdir(d):
                os.makedirs(d)
        for plugin in manifest.must_use_plugins():
            if plugin.name not in flags.exclude:
                progress("Installing mu-plugin {}".format(plugin.name))
                plugin.install(WP_MU_PLUGINS_INSTALL_DIR, rename_like_self=False)
        for plugin in manifest.plugins():
            if plugin.name not in flags.exclude:
                progress("Installing plugin {}".format(plugin.name))
                plugin.install(WP_PLUGINS_INSTALL_DIR)
        for theme in Themes.all():
            theme.install(WP_THEMES_INSTALL_DIR)
    else:
        Plugin(flags.name, [flags.path]).install('.')
