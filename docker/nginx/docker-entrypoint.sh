#!/bin/sh

set -e

if ! [ -f /etc/nginx/ssl/server.key -a -f /etc/nginx/ssl/server.cert ]; then
    mkdir -p /etc/nginx/ssl || true
    /usr/bin/openssl req -x509 -sha256 -nodes -days 3650 -newkey rsa:4096 -keyout /etc/nginx/ssl/server.key -out /etc/nginx/ssl/server.cert -subj "/C=CH/ST=Vaud/L=Lausanne/O=Ecole Polytechnique Federale de Lausanne (EPFL)/CN=*.epfl.ch"
fi

secrets_unchanged () {
    if [ -n "$oldpath" ]; then
        oldpaths="$(realpath /etc/nginx/generated-conf.d/*.conf)"
        return 0
    fi
    local newpaths
    newpaths="$(realpath /etc/nginx/generated-conf.d/*.conf)"
    if [ "$newpaths" != "$oldpaths" ]; then
        oldpaths="$newpaths"
        return 1
    fi
    return 0
}

# Whar supervisord? You are not the boss of me!
(while sleep 1; do if ! secrets_unchanged; then killall -HUP nginx; fi; done) &
/usr/sbin/php-fpm*
/usr/sbin/nginx
