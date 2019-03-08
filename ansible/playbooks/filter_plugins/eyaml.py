"""Decrypt secrets using Hiera's EYAML."""

import os
import subprocess


def eyaml(encrypted, keys):
    output = subprocess.check_output(
        ["eyaml", "decrypt",
         "--pkcs7-private-key", keys.priv,
         "--pkcs7-public-key", keys.pub,
         "-s", encrypted],
        stderr=open(os.devnull, 'w'))

    if "\n" not in output.rstrip():
        output = output.rstrip()

    return output


class FilterModule(object):
    def filters(self):
        return {'eyaml': eyaml}
