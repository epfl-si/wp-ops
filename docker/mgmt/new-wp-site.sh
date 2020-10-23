#!/bin/sh

set -e

: ${WORDPRESS_VERSION:=5.5}

usage() {
    die <<USAGE

Create a symlinked WordPress site into the current directory.

Usage: new-wp-site.sh

USAGE

}

main() {
    check_env_prereqs

    ( set -x; wp --path=. core symlink --path_to_version="/wp/$WORDPRESS_VERSION" )

    db_host="${MYSQL_DB_HOST:-db}"
    if [ -f wp-config.php ]; then
        # Retrieve DB credentials from wp-config.php
        eval "$(perl -ne 'm/(DB_(NAME|USER|PASSWORD)).*, '\''(.*)'\''/ && print lc($1) . "=$3\n";' < wp-config.php)"
    else
        db_name="wp_$(mkid 29)"
        db_user="$(mkid 16)"
        db_password="$(mkpass 20)"
        # `wp config create` doesn't care whether the credentials work or not
        ( set -x;
          extra_php_for_wp_config | wp --path=. config create \
             --dbname="$db_name" --dbuser="$db_user" --dbpass="$db_password" \
             --dbhost="$db_host" --extra-php --skip-check
        )
    fi

    ( set -x; wp db create --dbuser="$MYSQL_SUPER_USER" --dbpass="$MYSQL_SUPER_PASSWORD" ) || true

    echo "DROP USER '$db_user';" | do_mysql || true
    do_mysql <<SQL_CREATE_USER
CREATE USER '$db_user'@'%' IDENTIFIED BY '$db_password';
GRANT ALL PRIVILEGES ON $db_name.* TO '$db_user'@'%';
FLUSH PRIVILEGES;
SQL_CREATE_USER

    contents_of_symlinked_index_php > index.php

    if wp eval '1;' 2>&1 |grep "wp core install"; then
        do_wp_core_install
    fi

    ( set -x; wp eval '1;' )

}

###############################################################################

die () {
    if [ -n "$1" ]; then
        echo >&2 "$@"
    else
        cat >&2
    fi
    exit 2
}

check_env() {
    if [ -z "$MYSQL_SUPER_USER" -o -z "$MYSQL_SUPER_PASSWORD" ]; then
        die <<MISSING_ENV
Fatal: either MYSQL_SUPER_USER or MYSQL_SUPER_PASSWORD are unset.

Please source the appropriate .env file and try again.

MISSING_ENV
    fi
}

mkpass() {
    local length=$1
    pwgen -s "$length" -n 1
}

mkid() {
    local length=$1
    while true; do
        local id="$(mkpass $length | tr 'A-Z' 'a-z')"
        case "$id" in
            [a-z]*) echo "$id"; return 0;;
        esac
    done
}

whine_env() {
    die <<MESSAGE
Variable $1 is unset. Please source the appropriate .env file and try again.

MESSAGE
}

check_env_prereqs() {
    [ -n "$MYSQL_SUPER_USER" ] || whine_env "MYSQL_SUPER_USER"
    [ -n "$MYSQL_SUPER_PASSWORD" ] || whine_env "MYSQL_SUPER_PASSWORD"
    [ -n "$WP_ADMIN_USER" ] || whine_env "WP_ADMIN_USER"
    [ -n "$WP_ADMIN_EMAIL" ] || whine_env "WP_ADMIN_EMAIL"
}

do_mysql() {
    tee /dev/stderr | (set -x; mysql -h "${db_host}" -u "$MYSQL_SUPER_USER" -p"$MYSQL_SUPER_PASSWORD")
}

do_wp_core_install () {
    wp_hostname="$(pwd | cut -d/ -f4)"
    wp_path="$(pwd | cut -d/ -f6-)"

    local url
    if is_kubernetes; then
        url=https://$wp_hostname/$wp_path
    else
        url=http://$wp_hostname/$wp_path
    fi

    ( set -e -x
      wp core install --url="$url" \
         --title="$(basename "$(pwd)")" \
         --admin_user="$WP_ADMIN_USER" --admin_email="$WP_ADMIN_EMAIL" \
         --wpversion="$WORDPRESS_VERSION"

          # Configure permalinks
          wp rewrite structure '/%postname%/' --hard

          # Configure TimeZone
          wp option update timezone_string Europe/Zurich
          # Configure Time Format 24H
          wp option update time_format H:i
          # Configure Date Format d.m.Y
          wp option update date_format d.m.Y

          # Add french for the admin interface
          wp language core install fr_FR

          # remove unfiltered_upload capability. Will be reactivated during
          # export if needed.
          wp cap remove administrator unfiltered_upload

          # Disable avatars for security reason. Because a call to gravatar.com is done when user is logged and
          # hash with email address associated to account is given
          wp option update show_avatars ''

    )
    echo "$url"
}

is_kubernetes() {
    test -d /run/secrets/kubernetes.io/serviceaccount 2>/dev/null
}

contents_of_symlinked_index_php() {
    cat <<INDEX_PHP
<?php
/**
 * Front to the WordPress application. This file doesn't do anything, but loads
 * wp-blog-header.php which does and tells WordPress to load the theme.
 *
 * @package WordPress
 */

/**
 * Tells WordPress to load the WordPress theme and output it.
 *
 * @var bool
 */
define('WP_USE_THEMES', true);

/** Loads the WordPress Environment and Template */
require_once('wp/wp-blog-header.php');

INDEX_PHP
}

extra_php_for_wp_config () {
    cat <<"PHP"
if (isset( $_SERVER['HTTP_X_FORWARDED_PROTO'] ) &&
    $_SERVER['HTTP_X_FORWARDED_PROTO'] == 'https') {
    $_SERVER['HTTPS']='on';
}

define('ALLOW_UNFILTERED_UPLOADS', true);

PHP
}

main
