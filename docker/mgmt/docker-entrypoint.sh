#!/bin/bash

set -e -x

SECRETS_DIR=/var/lib/secrets/ssh

sync_keys() {
    cp -HL "$SECRETS_DIR"/authorized_keys /var/www/.ssh/
    chown -R www-data:www-data /var/www/.ssh
    chmod 0700 /var/www/.ssh

    cp -HL "$SECRETS_DIR"/*key "$SECRETS_DIR"/*key.pub /etc/ssh/
    chmod 0700 /etc/ssh/*key
    chown root:root /etc/ssh/*key /etc/ssh/*key.pub
}

iwait() {
    if inotifywait "$@"; then return 0; fi
    local exitcode="$?"
    case "$exitcode" in
        0|2) return 0 ;;   # 2 means timeout i.e. nothing happened
        *) return "$exitcode" ;;
    esac
}

################################################

if [ -d "$SECRETS_DIR" ]; then
    sync_keys

    /usr/sbin/sshd -D &
    SSHD_PID=$!
    while iwait -t 300 -r /var/lib/secrets/ssh; do
        sync_keys
        kill -HUP $SSHD_PID  # Will fail, and cause the whole script to exit,
                             # if sshd exited
    done
else
    # Development mode
    sleep infinity
fi

