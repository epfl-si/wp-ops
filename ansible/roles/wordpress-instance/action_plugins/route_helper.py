import subprocess
from urllib.parse import urlparse

def check_route_exist(openshift_namespace, route_name):
    """
    Return True if openshift route exists. Otherwise False.
    """
    command = f"oc -n {openshift_namespace} get routes {route_name} --no-headers --ignore-not-found=true | awk '{{print $1;}}'"

    result = subprocess.check_output(
        command,
        shell=True, 
        encoding='utf-8').rstrip('\n')

    return result == route_name

def getRouteName(site_url, openshift_env):
    """
    Get Openshift route name
    """

    # examples:
    # - https://ivea.epfl.ch => ivea
    # - https://www.nolossproject.eu  => www-nolossproject-eu
    site_name = urlparse(site_url).netloc.replace(".epfl.ch", "").replace(".", "-")
    if openshift_env.startswith("unm-"):
        route_name = f"httpd-unm-{site_name}"
    else:    
        route_name = f"httpd-{site_name}"
    return route_name
