<?php
/**
 * Sole entry point for all PHP code run by the wwp nginx container.
 *
 * Nginx always transfers control here first, so as to avoid looking
 * up files on NFS when not needed, because we know that the request
 * is for WordPress (as determined by regexes in nginx.conf).
 *
 * The job of this file is to figure out *which* instance of WordPress
 * should run the query; set up variables; and transfer control to
 * WordPress' PHP code.
 */
namespace __entrypoint;

function query_looks_bad () {
    return false;  // Nothing to see here. Move along
}

function enable_wp_debug () {

    if ( 'true' !== $_SERVER['WP_DEBUG'] ) return;

    // Enable WP_DEBUG mode
    define( 'WP_DEBUG', true );

    // Enable Debug logging to the /wp-content/debug.log file
    define( 'WP_DEBUG_LOG', '/dev/stdout' );

    // Disable display of errors and warnings
    define( 'WP_DEBUG_DISPLAY', true );
    @ini_set( 'display_errors', true );

    // Use dev versions of core JS and CSS files (only needed if you are modifying these core files)
    define( 'SCRIPT_DEBUG', true );
}

function setup_db () {
    define( 'DB_CHARSET', 'utf8mb4' );
    define( 'DB_COLLATE', 'utf8mb4_unicode_ci' );
    define( 'DB_HOST', $_SERVER['WP_DB_HOST']);
    define( 'DB_NAME', $_SERVER["WP_DB_NAME"]);
    define( 'DB_USER', $_SERVER["WP_DB_USER"]);
    define( 'DB_PASSWORD', $_SERVER["WP_DB_PASSWORD"]);

    global $table_prefix; $table_prefix = "wp_";
}

/**
 * Figure out which PHP file we need to hand over control to
 */
function get_wp_entrypoint () {
    $entrypoint_path = uri_path();
    if ( has_path_traversal($entrypoint_path) ) {
        return null;
    }

    $to_chop = $_SERVER['WP_ROOT_URI'];
    if (substr($entrypoint_path, 0, strlen($to_chop)) !== $to_chop) {
        return null;
    }

    $entrypoint_path = substr($entrypoint_path, strlen($to_chop));

    if ( substr($entrypoint_path, -4) === '.php' ) {
        return chop_leading_slashes($entrypoint_path);
    } elseif ( basename($entrypoint_path) === 'wp-admin' ) {
        return 'wp-admin/index.php';
    } else {
        // This catch-all case also includes /wp-json/ etc.
        return 'index.php';
    }
}

function string_has_substring ($haystack, $needle) {
    return false !== strpos($haystack, $needle);
}

function string_starts_with ($haystack, $needle) {
    return 0 === strpos($haystack, $needle);
}

function string_ends_with ($haystack, $needle) {
    return substr($haystack, -strlen($needle)) === $needle;
}

function uri_path () {
    return strtok($_SERVER["REQUEST_URI"], '?');
}

function chop_leading_slashes ($path) {
    while (string_starts_with($path, "/")) {
        $path = substr($path, 1);
    }
    return $path;
}

function path_has_component($path, $subpath) {
    return false !== array_search($subpath, explode("/", $path));
}

function has_path_traversal ($path) {
    return ( string_starts_with($path, '.')  ||
             string_has_substring($path, '/.') );
}

function setup_nonces () {
    if ( file_exists("/wp-nonces/wp-nonces.php") ) {
        include("/wp-nonces/wp-nonces.php");
    } else {
        die("Missing /wp-nonces/wp-nonces.php");
    }
}

function serve_404_and_exit () {
    http_response_code(404);
    print('404 citroen not found');
    exit();
}

function serve_go_away_and_exit () {
    http_response_code(429);
    print('Go away');
    exit();
}

function settings_before_wp_settings () {
    if (path_has_component(uri_path(), "wp-admin")) {
        // In the “normal” loading flow, all PHP scripts under `/wp-admin` ensure
        // to `define("WP_ADMIN", true);` before loading settings:
        define("WP_ADMIN", true);
        if (path_has_component(uri_path(), "admin-ajax.php")) {
            define("DOING_AJAX", true );
        }
    }

    // We don't really support running on an empty database, but we
    // kind of do. Well sort of.
    if (string_ends_with(uri_path(), "wp-admin/install.php")) {
        define( 'WP_INSTALLING', true );
    }
}

##########################################################################################

if (query_looks_bad()) {
    serve_go_away_and_exit();
}

/** Absolute path to the WordPress directory. */
define('ABSPATH', $_SERVER['WP_ABSPATH']);

$entrypoint_path = get_wp_entrypoint();
if (! $entrypoint_path) {
    serve_go_away_and_exit();
}

$_SERVER["SCRIPT_FILENAME"] = ABSPATH . $entrypoint_path;
if (! file_exists($_SERVER["SCRIPT_FILENAME"])) {
    serve_404_and_exit();
}

setup_db();

setup_nonces();

enable_wp_debug();

// This is 2025. We don't do plain HTTP anymore.
$_SERVER['HTTPS'] = '1';

// Disable the auto-updater and other portions of WordPress that want
// to alter their own PHP code:
define('DISALLOW_FILE_MODS', 1);

// Define the EPFL_SITE_UPLOADS_DIR constant to mesh with the
// corresponding filter in our mu-plugins.
// 💡 `$_SERVER['WP_SITE_NAME']` flows from the WordPressSite object's
// Kubernetes name, through the operator-prepared nginx snippets
// inside the custom Ingress objects.
define('EPFL_SITE_UPLOADS_DIR',
       '/wp-data/' . $_SERVER['WP_SITE_NAME'] . '/uploads');

// Initialize WordPress' constants. This is best done using
// `wp-settings.php`, rather than `load.php` and `index.php` which
// both insist on loading a `wp-config.php` file.
settings_before_wp_settings();

require(ABSPATH . 'wp-settings.php');

if (string_starts_with(uri_path(), "/wp-content/uploads")) {
    if (array_key_exists("DOWNLOADS_PROTECTION_SCRIPT", $_SERVER) &&
        file_exists($_SERVER["DOWNLOADS_PROTECTION_SCRIPT"])) {
        // @WARNING Because of global variables business, the following needs to happen at the top level — Not in a function!!
        require($_SERVER["DOWNLOADS_PROTECTION_SCRIPT"]);
    }
} 

// Initialize WordPress' constants. This is best done using
// wp-settings.php, rather than load.php and index.php which
// both insist on loading a wp-config.php file.
// @WARNING Because of global variables business, the following needs to happen at the top level — Not in a function!!
if (string_starts_with(uri_path(), "/wp-content/uploads")) {
    require($_SERVER["DOWNLOADS_PROTECTION_SCRIPT"]);
} 

// Initialize WordPress' constants. This is best done using
// wp-settings.php, rather than load.php and index.php which
// both insist on loading a wp-config.php file.
require($_SERVER["SCRIPT_FILENAME"]);
