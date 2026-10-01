#!/bin/bash

export WP_CLI_PACKAGES_DIR=/wp/wp-cli/packages
export WP_CLI_CONFIG_PATH=/wp/wp-cli/wp-cli-config.yml

# What wp-operator provisions for a WordpressSite (a MariaDB Database and User,
# and the Secret holding the user's password) is owned by it: find it through
# the `ownerReferences`, rather than by guessing names.
owned_by_site () {
    local plural="$1" site_uid="$2"
    kubectl get "$plural" -o json | \
        jq -c --arg uid "$site_uid" 'first(.items[] | select(any(.metadata.ownerReferences[]?; .uid == $uid)))'
}

php_quote () {
    local v="${1//\\/\\\\}"
    printf %s "${v//\'/\\\'}"
}

configure_site () {
    local site="$1"
    local wp_tmpdir="$(mktemp -d /tmp/wp-XXXXXX)"
    trap "rm -rf '$wp_tmpdir'" EXIT INT TERM

    export WP_CONFIG_PATH="$wp_tmpdir/wp-config.php"

    local site_uid database user
    site_uid="$(kubectl get wordpresssites.wordpress.epfl.ch "$site" -o jsonpath='{.metadata.uid}')" || exit 1
    database="$(owned_by_site databases.k8s.mariadb.com "$site_uid")"
    user="$(owned_by_site users.k8s.mariadb.com "$site_uid")"
    if [ -z "$database" ] || [ -z "$user" ]; then
        echo "wp: no Database or User owned by WordpressSite $site" >&2
        exit 1
    fi

    local db_host db_name db_user db_password
    db_host="$(jq -r '.spec.mariaDbRef.name' <<<"$database")"
    db_name="$(jq -r '.spec.name // .metadata.name' <<<"$database")"
    db_user="$(jq -r '.spec.name // .metadata.name' <<<"$user")"
    db_password="$(kubectl get secret "$(jq -r '.spec.passwordSecretKeyRef.name' <<<"$user")" \
                     -o jsonpath="{.data.$(jq -r '.spec.passwordSecretKeyRef.key' <<<"$user")}" | base64 -d)" || exit 1
    db_host="$(php_quote "$db_host")"
    db_name="$(php_quote "$db_name")"
    db_user="$(php_quote "$db_user")"
    db_password="$(php_quote "$db_password")"

    cat > "$WP_CONFIG_PATH" <<EOF
<?php

define( 'DB_NAME', '$db_name' );

/** Database username */
define( 'DB_USER', '$db_user' );

/** Database password */
define( 'DB_PASSWORD', '$db_password' );

/** Database hostname */
define( 'DB_HOST', '$db_host' );

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

declare -a wp_cli_args
while [ "$#" -gt 0 ]; do
  case "$1" in
      # --ingress is the old name: an Ingress is named after its WordpressSite
      --site|--ingress)
          configure_site "$2"
          shift; shift ;;
      --site=*|--ingress=*)
          configure_site "$(echo "$1" |cut -d= -f2-)"
          shift ;;
      *)
          wp_cli_args+=("$1")
          shift ;;
  esac
done


exec php /wp/wp-cli/wp-cli.phar "${wp_cli_args[@]}"
