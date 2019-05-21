"""CSV report on a bunch of WordPress instances."""

import csv as CSV
import io
import sys

EXAMPLES = """
- name: CSV inventory report
  local_action:
    module: copy
    dest: "./report.csv"
    content: '{{ hostvars | wp_inventory_csv_report }}'
"""


class FilterModule(object):
    def filters(self):
        return {
            'wp_inventory_csv_report': self.make_report
        }

    def make_report(self, hostvars, with_header_line=True):
        if (sys.version_info > (3, 0)):
            output = io.StringIO()
        else:
            # https://stackoverflow.com/a/13120279/435004
            output = io.BytesIO()

        m = ReportModel(hostvars)
        fields = ['name'] + ['plugin_version_%s' % n
                             for n in m.all_plugin_names]

        csv = CSV.DictWriter(output, fieldnames=fields)
        csv.writeheader()

        for name, host in m.iterhosts():
            csvrow = {'name': name}
            for p in host.plugins:
                csvrow['plugin_version_%s' % p.name] = p.version
            csv.writerow(csvrow)

        return output.getvalue()


class memoize:
    def __init__(self, wrapped):
        self._wrapped = wrapped

    def __call__(self, owner):
        cache_attr = '_memoized_%s' % self._wrapped.__name__
        if not hasattr(owner, cache_attr):
            setattr(owner, cache_attr, self._wrapped(owner))
        return getattr(owner, cache_attr)


def memoize_property(wat):
    return property(memoize(wat))


class ReportModel(object):
    def __init__(self, hostvars):
        self.hostvars = hostvars

    @memoize_property
    def all_plugin_names(self):
        return sorted(set(p.name for _unused, h in self.iterhosts()
                          for p in h.plugins))

    def iterhosts(self):
        for host, vars in self.hostvars.items():
            if "ansible_local" in vars["ansible_facts"]:
                yield host, self.Host(host, vars["ansible_facts"]["ansible_local"])

    class Host(object):
        def __init__(self, name, vars):
            self.name = name
            self.vars = vars
            self.plugins = []
            self.mu_plugins = []

            wp_plugin_list = self.vars.get("wp_plugin_list", None)
            if wp_plugin_list and isinstance(wp_plugin_list, type([])):
                for wp_plugin_list_entry in wp_plugin_list:
                    for subclass, bucket in (
                            (self.Plugin, self.plugins),
                            (self.MustUsePlugin, self.mu_plugins)):
                        if subclass.fits(wp_plugin_list_entry):
                            bucket.append(
                                subclass(wp_plugin_list_entry))

        class PluginBase(object):
            def __init__(self, wp_plugin_list_entry):
                assert self.fits(wp_plugin_list_entry)
                self.name    = wp_plugin_list_entry["name"]     # noqa
                self.version = wp_plugin_list_entry["version"]

        class Plugin(PluginBase):
            @classmethod
            def fits(cls, wp_plugin_list_entry):
                return wp_plugin_list_entry["status"] == "active"

        class MustUsePlugin(PluginBase):
            @classmethod
            def fits(cls, wp_plugin_list_entry):
                return wp_plugin_list_entry["status"] == "must-use"



################################  TEST SUITE ###########################
if __name__ == '__main__':
    hostvars = {
        "www-ventil2": {
            "ansible_facts": {
                "ansible_local": {
                    "wp_is_installed": "true",
                    "wp_is_symlinked": "true",
                    "wp_plugin_list": [
                        {
                            "name": "cache-control",
                            "status": "active",
                            "update": "none",
                            "version": "2.2.3"
                        },
                        {
                            "name": "epfl",
                            "status": "active",
                            "update": "none",
                            "version": "1.24"
                        },
                        {
                            "name": "epfl-404",
                            "status": "active",
                            "update": "none",
                            "version": "0.3"
                        },
                        {
                            "name": "EPFL-Share",
                            "status": "active",
                            "update": "none",
                            "version": "0.1"
                        },
                        {
                            "name": "accred",
                            "status": "active",
                            "update": "none",
                            "version": "0.13 (vpsi)"
                        },
                        {
                            "name": "EPFL-Content-Filter",
                            "status": "inactive",
                            "update": "none",
                            "version": "0.1.0"
                        },
                        {
                            "name": "EPFL-settings",
                            "status": "active",
                            "update": "none",
                            "version": "0.6"
                        },
                        {
                            "name": "epfl-infoscience",
                            "status": "active",
                            "update": "none",
                            "version": "1.5"
                        },
                        {
                            "name": "tequila",
                            "status": "active",
                            "update": "none",
                            "version": "0.15 (vpsi)"
                        },
                        {
                            "name": "ewww-image-optimizer",
                            "status": "active",
                            "update": "none",
                            "version": "4.7.4"
                        },
                        {
                            "name": "feedzy-rss-feeds",
                            "status": "active",
                            "update": "none",
                            "version": "3.3.6"
                        },
                        {
                            "name": "mainwp-child",
                            "status": "active",
                            "update": "none",
                            "version": "3.5.7"
                        },
                        {
                            "name": "wp-nested-pages",
                            "status": "active",
                            "update": "none",
                            "version": "3.0.11"
                        },
                        {
                            "name": "pdfjs-viewer-shortcode",
                            "status": "active",
                            "update": "none",
                            "version": "1.3"
                        },
                        {
                            "name": "polylang",
                            "status": "active",
                            "update": "none",
                            "version": "2.5.3"
                        },
                        {
                            "name": "varnish-http-purge",
                            "status": "active",
                            "update": "none",
                            "version": "4.8.1"
                        },
                        {
                            "name": "remote-content-shortcode",
                            "status": "active",
                            "update": "none",
                            "version": "1.4.3"
                        },
                        {
                            "name": "shortcode-ui",
                            "status": "active",
                            "update": "none",
                            "version": "0.7.4"
                        },
                        {
                            "name": "shortcode-ui-richtext",
                            "status": "active",
                            "update": "none",
                            "version": "1.3"
                        },
                        {
                            "name": "simple-sitemap",
                            "status": "active",
                            "update": "none",
                            "version": "3.0"
                        },
                        {
                            "name": "svg-support",
                            "status": "active",
                            "update": "none",
                            "version": "2.3.15"
                        },
                        {
                            "name": "tinymce-advanced",
                            "status": "active",
                            "update": "none",
                            "version": "5.2.0"
                        },
                        {
                            "name": "very-simple-meta-description",
                            "status": "active",
                            "update": "none",
                            "version": "5.4"
                        },
                        {
                            "name": "wordpress-importer",
                            "status": "active",
                            "update": "none",
                            "version": "0.6.4"
                        },
                        {
                            "name": "wp-media-folder",
                            "status": "active",
                            "update": "available",
                            "version": "4.7.11"
                        },
                        {
                            "name": "EPFL_stats_loader",
                            "status": "must-use",
                            "update": "none",
                            "version": "1.5"
                        },
                        {
                            "name": "EPFL_custom_editor_menu",
                            "status": "must-use",
                            "update": "none",
                            "version": "0.0.1"
                        },
                        {
                            "name": "EPFL_disable_updates_automatic",
                            "status": "must-use",
                            "update": "none",
                            "version": "0.0.1"
                        },
                        {
                            "name": "EPFL_disable_comments",
                            "status": "must-use",
                            "update": "none",
                            "version": "0.2"
                        },
                        {
                            "name": "EPFL_enable_updates_automatic",
                            "status": "must-use",
                            "update": "none",
                            "version": "0.0.1"
                        },
                        {
                            "name": "epfl-functions",
                            "status": "must-use",
                            "update": "none",
                            "version": "0.0.7"
                        },
                        {
                            "name": "EPFL_google_analytics_hook",
                            "status": "must-use",
                            "update": "none",
                            "version": "1.0"
                        },
                        {
                            "name": "EPFL_installs_locked",
                            "status": "must-use",
                            "update": "none",
                            "version": "0.0.4"
                        },
                        {
                            "name": "EPFL_quota_loader",
                            "status": "must-use",
                            "update": "none",
                            "version": "0.4"
                        },
                        {
                            "name": "EPFL_jahia_redirect",
                            "status": "must-use",
                            "update": "none",
                            "version": "1.3"
                        }
                    ]
                }
            }
        }
    }
    print(FilterModule().make_report(hostvars, with_header_line=True))
