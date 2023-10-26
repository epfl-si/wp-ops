from urllib.parse import urlparse

class FilterModule(object):
    def filters(self):
        return {
            "hostname_of_url": self.hostname_of_url,
            "route_name": self.route_name
        }

    def hostname_of_url(self, site_url):
        return urlparse(site_url).netloc

    def route_name(self, site_url, openshift_env):
        site_name = urlparse(site_url).netloc.replace(".epfl.ch", "").replace(".", "-")
        route_name = f"httpd-{site_name}"
        return route_name
