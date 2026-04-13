#!/usr/bin/env bash

# Patch wp-cli.phar at container creation time

set -euo pipefail

do_patch () {
    sed -i 's|\(ini_set.*memory_limit.*-1.*\)|// \1|' \
        vendor/wp-cli/wp-cli/php/WP_CLI/Runner.php
}

echo "phar.readonly = Off" >> /etc/php/*/cli/php.ini

PHAR="$1"
WORKDIR="$(mktemp -d)"

trap "rm -rf '$WORKDIR'" HUP QUIT TERM EXIT
cd "$WORKDIR"

phar extract -f "$PHAR"
do_patch
phar pack -f "$PHAR" .
