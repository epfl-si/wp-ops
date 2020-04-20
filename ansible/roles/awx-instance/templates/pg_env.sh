{# Canned shell command to extract the Django database secrets using
 # Python,and output them to stdout as environment variables in Bourne
 # Shell format
 #}
{% set python_script = '
import subprocess
import shlex
from credentials import DATABASES

pg = DATABASES["default"]

for k in ["NAME", "HOST", "PORT", "USER", "PASSWORD"]:
    print("DATABASE_%s=%s" % (k, shlex.quote(pg[k])))

' %}
{# Canned command may not contain single quotes, lest it be
 # munged by the local shell (which we can't just bypass, because
 # we need stdin / stdout redirection).
 #}
{% set python_script_quoted = python_script | regex_replace('"', '\\\\"') %}
env PYTHONPATH=/etc/tower/conf.d {{ ansible_python_interpreter }} -c "{{ python_script_quoted }}"
