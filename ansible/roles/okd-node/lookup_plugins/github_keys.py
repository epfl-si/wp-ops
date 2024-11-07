import urllib.request
from ansible.plugins.lookup import LookupBase

def urlget(u):
    with urllib.request.urlopen(u) as response:
        return response.read().decode("utf-8")

class LookupModule (LookupBase):
    def run (self, terms, variables, *args):
        ret = ""
        github_usernames = terms[0]
        for u in github_usernames:
            keys = urlget(f'https://github.com/{ u }.keys')

            if not keys.endswith("\n"):
                keys = keys + "\n"
            ret = ret + keys
        return [ ret ]   # For some reason, Ansible insists on returning an array out of lookup modules
