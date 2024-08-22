{#
 # Tips and tricks to feed into sh(1) so as to work around the rampant
 # seccomp breakage in end-of-lifed OpenShift 3
 # (https://github.com/moby/moby/issues/42680)
 #
 # 💡 The bizarre extraneous semicolons are here so that the script
 # supports being folded into a single line, for Dockerfile `RUN` bliss.
 #}

install_it () {
   pip3 install requests >&2 ;
} ;

poorcurl () {
    python3 -c 'import requests; import sys; sys.stdout.buffer.write(requests.get(url = sys.argv[-1]).content)' -- "$@" ;
} ;

download_github_release () {
   poorcurl $(poorcurl "https://api.github.com/repos/$1/releases" \
            | python3 -c \
              "import sys; import json; import re; \
               release = (r for r in json.load(sys.stdin) if r['name'] == '$2').__next__(); \
               asset = (a for a in release['assets'] if a['name'].endswith('$3')).__next__(); \
               print(asset['browser_download_url'])") ;
}
