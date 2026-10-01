#!/bin/bash

export WP_CLI_PACKAGES_DIR=/wp/wp-cli/packages
export WP_CLI_CONFIG_PATH=/wp/wp-cli/wp-cli-config.yml

# Writes $WP_CONFIG_PATH out of the $WP_DB_* variables
write_wp_config () {
    cat > "$WP_CONFIG_PATH" <<EOF
<?php

define( 'DB_NAME', '$WP_DB_NAME' );

/** Database username */
define( 'DB_USER', '$WP_DB_USER' );

/** Database password */
define( 'DB_PASSWORD', '$WP_DB_PASSWORD' );

/** Database hostname */
define( 'DB_HOST', '$WP_DB_HOST' );

/** Database charset to use in creating database tables. */
define( 'DB_CHARSET', 'utf8' );

/** The database collate type. Don't change this if in doubt. */
define( 'DB_COLLATE', '' );

EOF
    cat >> "$WP_CONFIG_PATH" <<'EOF'


/**#@-*/

/**
 * WordPress database table prefix.
 *
 * You can have multiple installations in one database if you give each
 * a unique prefix. Only numbers, letters, and underscores please!
 */
$table_prefix = 'wp_';


/* Add any custom values between this line and the "stop editing" line. */



/**
 * For developers: WordPress debugging mode.
 *
 * Change this to true to enable the display of notices during development.
 * It is strongly recommended that plugin and theme developers use WP_DEBUG
 * in their development environments.
 *
 * For information on other constants that can be used for debugging,
 * visit the documentation.
 *
 * @link https://wordpress.org/support/article/debugging-in-wordpress/
 */
if ( ! defined( 'WP_DEBUG' ) ) {
	define( 'WP_DEBUG', false );
}

/* That's all, stop editing! Happy publishing. */

/** Absolute path to the WordPress directory. */
if ( ! defined( 'ABSPATH' ) ) {
	define( 'ABSPATH', __DIR__ . '/' );
}

/** Sets up WordPress vars and included files. */
require_once ABSPATH . 'wp-settings.php';
EOF
}

configure_ingress () {
    local wp_tmpdir="$(mktemp -d /tmp/wp-XXXXXX)"
    trap "rm -rf '$wp_tmpdir'" EXIT INT TERM

    export WP_CONFIG_PATH="$wp_tmpdir/wp-config.php"
    kubectl get -o jsonpath="{.metadata.annotations['nginx\.ingress\.kubernetes\.io/configuration-snippet'] }" ingress/"$1" | \
        perl -ne 'next unless m/^fastcgi_param (WP_DB_\S*?)\s+(\S*)/; print "$1=$2\n"' | \
    (
        eval "$(cat)"
        write_wp_config
    )
}

# What wp-operator provisions for a WordpressSite (a MariaDB Database and User,
# and the Secret holding the user's password) is owned by it: find it through
# the `ownerReferences`.
owned_by_site () {
    local plural="$1" site_uid="$2"
    kubectl get "$plural" -o json | \
        jq -c --arg uid "$site_uid" 'first(.items[] | select(any(.metadata.ownerReferences[]?; .uid == $uid)))'
}

# Values go between single quotes in PHP
php_quote () {
    local v="${1//\\/\\\\}"
    printf %s "${v//\'/\\\'}"
}

# Prints the $WP_DB_* assignments for the named WordpressSite, ready to `eval`
site_credentials () {
    local site="$1" site_uid database user
    site_uid="$(kubectl get wordpresssites.wordpress.epfl.ch "$site" -o jsonpath='{.metadata.uid}')" || return 1
    database="$(owned_by_site databases.k8s.mariadb.com "$site_uid")"
    user="$(owned_by_site users.k8s.mariadb.com "$site_uid")"
    if [ -z "$database" ] || [ -z "$user" ]; then
        echo "wp: no Database or User owned by WordpressSite $site" >&2
        return 1
    fi

    local password
    password="$(kubectl get secret "$(jq -r '.spec.passwordSecretKeyRef.name' <<<"$user")" \
                  -o jsonpath="{.data.$(jq -r '.spec.passwordSecretKeyRef.key' <<<"$user")}" | base64 -d)" || return 1
    printf 'WP_DB_HOST=%q\n' "$(php_quote "$(jq -r '.spec.mariaDbRef.name' <<<"$database")")"
    printf 'WP_DB_NAME=%q\n' "$(php_quote "$(jq -r '.spec.name // .metadata.name' <<<"$database")")"
    printf 'WP_DB_USER=%q\n' "$(php_quote "$(jq -r '.spec.name // .metadata.name' <<<"$user")")"
    printf 'WP_DB_PASSWORD=%q\n' "$(php_quote "$password")"
}

configure_site () {
    local credentials
    credentials="$(site_credentials "$1")" || exit 1

    local wp_tmpdir="$(mktemp -d /tmp/wp-XXXXXX)"
    trap "rm -rf '$wp_tmpdir'" EXIT INT TERM

    export WP_CONFIG_PATH="$wp_tmpdir/wp-config.php"
    (
        eval "$credentials"
        write_wp_config
    )
}

declare -a wp_cli_args
while [ "$#" -gt 0 ]; do
  case "$1" in
      --ingress)
          configure_ingress "$2"
          shift; shift ;;
      --ingress=*)
          configure_ingress "$(echo "$1" |cut -d= -f2-)"
          shift ;;
      --site)
          configure_site "$2"
          shift; shift ;;
      --site=*)
          configure_site "$(echo "$1" |cut -d= -f2-)"
          shift ;;
      *)
          wp_cli_args+=("$1")
          shift ;;
  esac
done


exec php /wp/wp-cli/wp-cli.phar "${wp_cli_args[@]}"
