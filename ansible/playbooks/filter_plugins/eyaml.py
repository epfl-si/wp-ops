"""Decrypt secrets using Hiera's EYAML."""

import subprocess

from ansible.errors import AnsibleFilterError


def eyaml(encrypted, keys):
    cmd = ["eyaml", "decrypt",
           "--pkcs7-private-key", keys['priv'],
           "--pkcs7-public-key", keys['pub']]
    proc = subprocess.run(
        cmd + ["-s", encrypted],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding="utf-8",
        check=True)

    # What a nice surprise: eyaml doesn't manage its exit code correctly.
    output = proc.stdout

    if (not output) and " @ " in proc.stderr:
        raise AnsibleFilterError("Error running %s: %s" %
                                 (" ".join(cmd + ["-s", "..."]),
                                  proc.stderr))

    if "\n" not in output.rstrip():
        output = output.rstrip()

    return output


class FilterModule(object):
    def filters(self):
        return {'eyaml': eyaml}
