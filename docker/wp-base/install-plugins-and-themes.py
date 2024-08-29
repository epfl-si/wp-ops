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
import operator
from distutils.version import LooseVersion

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

      --manifest-url <url>       The URL to obtain the plugin manifest from;
                                 default is %s

      --s3-endpoint-url <url>    The URL of the S3 server that holds the
                                 purchased assets (plugins or other).
      --s3-region <region>       The S3 region to use
      --s3-bucket <url>          The bucket name where the purchased assets reside
      --s3-key-id <s3keyid>
      --s3-secret <s3secret>     Credentials used to access the assets on S3
                                 (those whose `from:` start with s3://).
                                 You can alternatively set environment variables
                                 AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY (just
                                 like `aws cp` expects).
                                 
      --wp-version               The wp version this install is running for

  install-plugins-and-themes.py <name> <URL>

    Install one plugin or theme into the current directory. <name> is
    the name of the subdirectory to create. <URL> can point to a ZIP
    file, a GitHub URL (possibly pointing to a particular branch and
    subdirectory), or it can be the string "wordpress.org/plugins",
    meaning that the plug-in named <name> shall be downloaded
    from the WordPress plugin repository.
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

    def __init__(self, url, branch=None):
        """Class constructor.

        @param url The URL to `git clone` from. Shall start with
        `https://github.com`; may contain a branch (e.g.
        `https://github.com/foo/bar/tree/mybranch`) and a path to a
        subdirectory (e.g. `https://github.com/foo/bar/tree/mybranch/sub/dir`)
        """
        self.url = url
        self._branch = branch
        self._parsed = self._parse(url)
        assert self._parsed

    @classmethod
    def is_valid(cls, url):
        return bool(cls._parse(url))

    @classmethod
    def _parse(cls, url):
        for parse_re in (
                'https://github.com/([^/]*)/([^/]*)/(?:tree|blob)/((?:(?:feature|bugfix|update)/)?[^/]+)(?:$|/(.*))',
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
        if self._branch:
            return self._branch
        else:
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
                git_clone_cmd = ["git", "clone", "--single-branch"]
                if self.branch is not None:
                    git_clone_cmd.extend(["-b", self.branch, self.clone_url])
                else:
                    git_clone_cmd.extend([self.clone_url])
                run_cmd(git_clone_cmd, cwd=str(tmp))
                self._git_topdir = os.path.join(str(tmp), self.github_project)
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

    def __init__(self, name, urls, **uncommon_kwargs):
        self.name = name
        self.urls = urls

    def __new__(cls, name, urls, **uncommon_kwargs):
        if cls is Plugin:
            cls = cls._find_handler(urls[0])

        that = object.__new__(cls)
        that.__init__(name, urls, **uncommon_kwargs)
        return that

    def get_skip_reason(self, flags):
        if self.name in flags.exclude:
            return "Skipped due to --exclude command-line flag"

    @staticmethod
    def subclasses():
        return (S3Plugin, ZipPlugin, GitHubPlugin, WordpressOfficialPlugin)

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

    def __init__(self, name, urls, **uncommon_kwargs):
        super(ZipPlugin, self).__init__(name, urls, **uncommon_kwargs)
        assert len(self.urls) == 1
        self.url = self.urls[0]
        assert self.url.startswith("http")

    def install(self, target_dir, rename_like_self=True):
        """Unzip into `target_dir`.

        Keyword arguments:
        rename_like_self -- Ignored - We always unzip to a subdirectory named
                            `self.name`
        """
        zipfd = io.BytesIO(requests.get(self.url).content)
        progress("Unzipping {}".format(self.url))
        self.install_from_fd(self.name, zipfd, target_dir)

    @classmethod
    def install_from_fd(cls, name, fd, target_dir):
        zip = ZipFile(fd)

        for member in zip.namelist():
            zipinfo = zip.getinfo(member)
            if zipinfo.filename[-1] == '/':
                continue

            targetpathelts = os.path.normpath(zipinfo.filename).split('/')
            targetpathelts[0] = name

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

    def __init__(self, name, urls, **uncommon_kwargs):
        super(GitHubPlugin, self).__init__(name, urls, **uncommon_kwargs)
        branch = uncommon_kwargs.get('branch')
        self._gits = [GitHubCheckout(url, branch) for url in self.urls]

    def install(self, target_dir, rename_like_self=True):
        """Install by copying into `target_dir`.

        Keyword arguments:
        rename_like_self -- if set, rename the top-level directory to `self.name`.
                            (Ignored if the plug-in consists of a single file)
        """
        for git in self._gits:
            self._copytree_install(git.clone().source_path, target_dir,
                                   rename_dir=self.name if rename_like_self else None)


class S3Plugin(Plugin):
    """A plug-in to obtain from an S3 bucket."""

    @classmethod
    def handles(cls, url):
        return url.startswith("s3://")

    client = None

    @classmethod
    def set_client(cls, client):
        cls.client = client

    def __init__(self, name, urls, **uncommon_kwargs):
        super(S3Plugin, self).__init__(name, urls, **uncommon_kwargs)
        assert len(self.urls) == 1
        self.url = self.urls[0]
        assert self.handles(self.url)

    def install(self, target_dir, rename_like_self=True):
        """Unzip into `target_dir`.

        Keyword arguments:
        rename_like_self -- Ignored - We always unzip to a subdirectory named
                            `self.name`
        """
        tmpzip = "/tmp/%s.zip" % self.name
        self.client.run_command("cp", self.url, tmpzip)
        ZipPlugin.install_from_fd(self.name, open(tmpzip, 'rb'), target_dir)
        os.unlink(tmpzip)


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
                   ['https://github.com/epfl-si/wp-theme-2018/tree/master/wp-theme-light'])
        )


class WpOpsPlugins:
    """Models the plugins enumerated in the "wp-ops" Ansible configuration."""

    # big up to "stack questions/31999444" for this
    OPERATORS = {
        '<': operator.lt,
        '<=': operator.le,
        '>': operator.gt,
        '>=': operator.ge,
        '==': operator.eq,
        '!=': operator.ne,
        # 'in' is using a lambda because of the opposite operator order
        # 'in': (lambda item, container: operator.contains(container, item),
        'in': (lambda item, container: item in container),
        'contains': operator.contains,
    }

    def __init__(self, manifest_url=None, wp_version=None):
        if manifest_url is None:
            manifest_url = AUTO_MANIFEST_URL
        progress("Obtaining plug-in manifest from {}".format(manifest_url))
        req = requests.get(manifest_url)
        if req.status_code != 200:
            raise Exception('requests.get("{}") yielded status {}'.format(
                manifest_url, req.status_code))
        self.plugins_yaml = req.content

        self.wp_version = wp_version

    def _plugins_and_is_mu(self):
        for thing in yaml.load(self.plugins_yaml, yaml.FullLoader):
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
            uncommon_kwargs = {}  # the others entries, for some specific implementation
            if options.get('branch'):
                uncommon_kwargs['branch'] = options['branch']
            if isinstance(urls, string_types):
                urls = [urls]

            # here is the ansible 'when' directive managed. Used to
            # filter by WP version, on the the 'wp_version_lineage' var
            when = thing.get('when', '').strip()
            if self.wp_version and when and 'wp_version_lineage' in when:
                try:
                    regex = r"version\(\s?['\"](.*)['\"]\s?,\s?['\"\s](.*)['\"]\s?\)\s?"
                    groups = re.search(regex, when).groups()
                    when_part_version = groups[0]
                    when_part_operator = groups[1]
                except Exception as e:
                    import pprint
                    raise Exception(pprint.pformat(thing))
                # install only if the 'when' condition is met
                if self.OPERATORS[when_part_operator](LooseVersion(self.wp_version), LooseVersion(when_part_version)):
                    yield (Plugin(name, urls, **uncommon_kwargs), is_mu)
            else:
                # go for it without any conditions !
                yield (Plugin(name, urls, **uncommon_kwargs), is_mu)

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
                opts, args = getopt.getopt(argv[1:], "e:v", [
                    "exclude=", "manifest-url=",
                    "s3-endpoint-url=", "s3-region=", "s3-bucket-name=",
                    "s3-key-id=", "s3-secret=", "wp-version="])
            except getopt.GetoptError:
                usage()
                sys.exit(1)
            self.exclude = set(a for o, a in opts if o in ("-e", "--exclude"))
            self.manifest_url = None
            for o, a in opts:
                if o == "--manifest-url":
                    self.manifest_url = a
                elif o == "--wp-version":
                    self.wp_version = a
            opts_dict = dict(opts)
            if "--s3-endpoint-url" in opts_dict:
                self.s3 = S3(opts_dict["--s3-endpoint-url"],  # Mandatory
                             opts_dict.get("--s3-region", None),
                             opts_dict["--s3-bucket-name"],
                             # The other two default to the awscli-style
                             # environment variables:
                             opts_dict.get("--s3-key-id", None),
                             opts_dict.get("--s3-secret", None))
            else:
                self.s3 = None
        else:
            self.name = argv[0]
            self.path = argv[1]

class S3:
    """Models an S3 bucket client."""
    def __init__(self, endpoint, region, bucket_name, keyid, secret):
        self.endpoint = endpoint
        self.region = region
        self.bucket_name = bucket_name
        self.keyid = keyid   or os.environ["AWS_ACCESS_KEY_ID"]
        self.secret = secret or os.environ["AWS_SECRET_ACCESS_KEY"]

    def run_command(self, *args):
        # Poor man's Jinja:
        args = [re.sub('\{\{.*\}\}', self.bucket_name, arg)
                for arg in args]
        cmd = ["aws", "--endpoint-url=%s" % self.endpoint]
        if self.region is not None:
            cmd.append("--region=%s" % self.region)
        cmd.append("s3")
        cmd.extend(args)
        return run_cmd(
            cmd,
            env=dict(
                AWS_ACCESS_KEY_ID=self.keyid,
                AWS_SECRET_ACCESS_KEY=self.secret))


WP_INSTALL_DIR = './wp-content'
WP_PLUGINS_INSTALL_DIR = os.path.join(WP_INSTALL_DIR, 'plugins')
WP_MU_PLUGINS_INSTALL_DIR = os.path.join(WP_INSTALL_DIR, 'mu-plugins')
WP_THEMES_INSTALL_DIR = os.path.join(WP_INSTALL_DIR, 'themes')


if __name__ == '__main__':
    flags = Flags()

    if flags.auto:
        S3Plugin.set_client(flags.s3)

        manifest = WpOpsPlugins(flags.manifest_url, flags.wp_version)
        for d in (WP_PLUGINS_INSTALL_DIR, WP_MU_PLUGINS_INSTALL_DIR):
            if not os.path.isdir(d):
                os.makedirs(d)
        for plugin in manifest.must_use_plugins():
            if plugin.name not in flags.exclude:
                progress("Installing mu-plugin {}".format(plugin.name))
                plugin.install(WP_MU_PLUGINS_INSTALL_DIR, rename_like_self=False)
        for plugin in manifest.plugins():
            skip_reason = plugin.get_skip_reason(flags)
            if skip_reason:
                progress("Skipping plugin {}: {}".format(plugin.name, skip_reason))
            else:
                progress("Installing plugin {}".format(plugin.name))
                plugin.install(WP_PLUGINS_INSTALL_DIR)
        for theme in Themes.all():
            theme.install(WP_THEMES_INSTALL_DIR)
    else:
        Plugin(flags.name, [flags.path]).install('.')
