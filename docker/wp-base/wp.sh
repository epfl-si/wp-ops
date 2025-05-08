#!/bin/bash

export WP_CLI_PACKAGES_DIR=/wp/wp-cli/packages
export WP_CLI_CONFIG_PATH=/wp/wp-cli/wp-cli-config.yml

configure_ingress () {
    local wp_tmpdir="$(mktemp -d /tmp/wp-XXXXXX)"
    trap "rm -rf '$wp_tmpdir'" EXIT INT TERM

    export WP_CONFIG_PATH="$wp_tmpdir/wp-config.php"
    kubectl get -o jsonpath="{.metadata.annotations['nginx\.ingress\.kubernetes\.io/configuration-snippet'] }" ingress/"$1" | \
        perl -ne 'next unless m/^fastcgi_param (WP_DB_\S*?)\s+(\S*)/; print "$1=$2\n"' | \
    (
        eval "$(cat)"
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
    )
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
      --ingress)
          configure_ingress "$2"
          shift; shift ;;
      --ingress=*)
          configure_ingress "$(echo "$1" |cut -d= -f2-)"
          shift ;;
      *)
          wp_cli_args+=("$1")
          shift ;;
  esac
done


exec php /wp/wp-cli/wp-cli.phar "${wp_cli_args[@]}"
