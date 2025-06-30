#!/bin/bash

echo "Starting nginx redirect server..."

/usr/local/bin/generate-nginx-config.sh

if [ -f /config/redirects.txt ]; then
    echo "Starting config file watcher..."
    (
        while inotifywait -e modify /config/redirects.txt 2>/dev/null; do
            echo "Config file changed, reloading..."
            /usr/local/bin/generate-nginx-config.sh
            nginx -s reload
        done
    ) &
fi

exec nginx -g 'daemon off;'
