<?php
/**
 * In order to create the databases, its tables and put some content in it, the
 * operator need to call this script. This script is basically a minimalistic
 * "wp cli" that instanciate the WordPress framework and call the same functions
 * that the installer does, but does not require to have a valid WordPress
 * installation (a `wp-config.php` and `wp-includes/version.php` as the "wp cli"
 * does).
 *
 * As it's calling WordPress code, the `ABSPATH` constant has to be correctly
 * defined. It's meant to stand in the root of the wp-dev directory, but feel
 * free to have it pointing to any directory containing an extract of an
 * WordPress source. See the __WORDPRESS_SOURCE_DIR constant to change it.
 *
 * It also have to be able to connect to the database, so name equivalent to
 * `DB.wordpress-test.svc` have to be accessible. It means that if you want it
 * to work from outside the cluster, you have to use something like KubeVPN.
**/

define( '__WORDPRESS_SOURCE_DIR', '/volumes/wp/6/' );
define( '__WORDPRESS_DOMAIN', 'wpn.fsd.team' );
define( '__WORDPRESS_DEFAULT_THEME', 'wp-theme-2018' );

define( '__WP_DB_FQDN', 'mariadb-min.wordpress-test.svc' );
define( '__WP_DB_NAME_PREFIX', 'wp-db-' );
define( '__WP_DB_USER_PREFIX', 'wp-db-user-' );

$shortops = "h";
$longopts  = array(
    "name:",
    "path:",
    "title::",
    "tagline::",
    "theme::",
);
$options = getopt($shortops, $longopts);
if ( empty($options["name"]) || empty($options["path"]) ) {
  echo '"--name" and "--path" are required arguments.';
  exit(1);
}
if ( empty($options["title"]) ) {
  $options["title"] = $options["name"];
}
if ( key_exists("h", $options) ) {
  echo 'ensure-wordpress-and-theme.php --name="site-a" --path="/site-A" --title="Titre du site A" --tagline="Tagline du super site A"';
  exit();
}
define( 'WP_CONTENT_DIR', dirname(__FILE__));
define( 'ABSPATH', dirname(__FILE__) . __WORDPRESS_SOURCE_DIR );
define( 'WP_DEBUG', 1);
define( 'WP_DEBUG_DISPLAY', 1);

function ensure_clean_site_url($path) {
  $site_url = __WORDPRESS_DOMAIN . "/{$path}/";
  return preg_replace('#/+#','/', $site_url);
}
define("WP_SITEURL", "https://" . ensure_clean_site_url($options["path"]));

$_SERVER['HTTP_HOST'] = __WORDPRESS_DOMAIN;

define("DB_USER", __WP_DB_USER_PREFIX . $options["name"] );
define("DB_PASSWORD", "secret"); // FIXME
define("DB_NAME", __WP_DB_NAME_PREFIX . $options["name"] );
define("DB_HOST", __WP_DB_FQDN);

global $table_prefix; $table_prefix = "wp_";

define("WP_ADMIN", true);
define("WP_INSTALLING", true);
require_once( ABSPATH . 'wp-settings.php' );

function ensure_db_schema () {
  require_once( ABSPATH . 'wp-admin/includes/upgrade.php' );
  if (! is_blog_installed()) {
    make_db_current_silent();
  }
  populate_options();
  populate_roles();
  wp_upgrade();
}

function ensure_admin_user ($user_name, $user_email, $user_password) {
  if (! username_exists($user_name)) {
    wp_create_user( $user_name, $user_password, $user_email );
  }
  $user = new WP_User( username_exists($user_name) );
  $user->set_role( 'administrator' );
  update_option( 'admin_email', $user_email );
}

function get_admin_user_id () {
  return 1;  // wp-cli does same
}

/**
 * Whatever wp_install does, that was not already done above.
 */
function ensure_other_basic_wordpress_things () {
  update_option( 'blog_public', 1 );
  update_option( 'fresh_site', 1 );
  update_option( 'siteurl', wp_guess_url() );

  wp_install_defaults( get_admin_user_id() );
  wp_install_maybe_enable_pretty_permalinks();

  flush_rewrite_rules();

  wp_cache_flush();
}

function ensure_site_title ( $options ) {
  update_option( 'blogname', stripslashes($options["title"]) );
}

function ensure_tagline ( $options ) {
  if ( !empty($options["tagline"]) ) {
    update_option( 'blogdescription', stripslashes($options["tagline"]) );
  }
}

function ensure_theme ( $options ) {
  if ( empty( $options[ 'theme' ] ) ) {
    $options[ 'theme' ] = __WORDPRESS_DEFAULT_THEME;
  }
  global $wp_theme_directories; $wp_theme_directories = [];
  require_once( ABSPATH . 'wp-includes/theme.php' );

  $theme = wp_get_theme( $options[ 'theme' ] );
  print( switch_theme( $theme->get_stylesheet() ) );
}

ensure_db_schema();
ensure_other_basic_wordpress_things();
ensure_admin_user("admin", "admin@exemple.com", "secret");
ensure_site_title( $options );
ensure_tagline( $options );
ensure_theme( $options );
