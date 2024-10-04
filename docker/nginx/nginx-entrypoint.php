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

function enable_wp_debug ($wordpress) {

    if ( false === $wordpress['wp_debug'] ) return;

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

function setup_db ($wordpress) {
    $db_credentials = get_db_credentials($wordpress);
    define( 'DB_CHARSET', 'utf8mb4' );
    define( 'DB_COLLATE', 'utf8mb4_unicode_ci' );
    define( 'DB_HOST', $db_credentials["db_host"]);
    define( 'DB_NAME', $db_credentials["db_name"]);
    define( 'DB_USER', $db_credentials["db_user"]);
    define( 'DB_PASSWORD', $db_credentials["db_password"]);

    global $table_prefix; $table_prefix = "wp_";
}

/**
 * Figure out which PHP file we need to hand over control to
 */
function get_wp_entrypoint ($wordpress) {
    $entrypoint_path = uri_path();
    if ( has_path_traversal($entrypoint_path) ) {
        return null;
    }

    $to_chop = $wordpress['site_uri'];
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

function setup_nonces ($wordpress) {
    // TODO: Read these up from another JSON Secret
    // NOTE: They can be generated by https://api.wordpress.org/secret-key/1.1/salt/
    define( 'AUTH_KEY',         '_#yH+/R.)X%;`*(4u=gy|Jo5`d8Gj)/1FaU[haP9P$48;v]1Eg7&zk:]nspMKuA#' );
    define( 'SECURE_AUTH_KEY',  'c&%V:8FXis7@;>l+2+FSUGYS?wG01r@W?&jq!V0-z:79A_W{*5CfSYf5{F&3FR!a' );
    define( 'LOGGED_IN_KEY',    'R@d4lS~LwB+:z$n{WN]#K:im_)7DT/~zhQw3S, YSTsl,-?k4/i_<t}rk*Dg) CI' );
    define( 'NONCE_KEY',        'RB~Xw1<TjGLru*w>PC2-fl1h .8>aY|9sa8x7-tm7]Psh{XY!I?Te<_b@qUQ=:mO' );
    define( 'AUTH_SALT',        'pj;f>C9/>dI|978`z@bI)}eb$2~3/:P<g~wd3k%=tbp-O`![td}6z{<{~L73=Fw2' );
    define( 'SECURE_AUTH_SALT', 'p|8ugKn38lKR0/XSt(LaR;}[Rsr}8,|b|BFG^_`N^BHGV?8N{O3d9XH~v5FYHl}i' );
    define( 'LOGGED_IN_SALT',   '{2Y,4WGBE6wT$gdOD.n)duoV5:Jm5d?L@p{`,^HorJ5`>zaprEqc;<]W|d7-T?zE' );
    define( 'NONCE_SALT',       'mVSh!um&7*qGB%sZ,gg6KDD!ko<s,e1Dj>X[CP+fR6<f(&iy[#?~y VBuS^${/&Q' );
}

function serve_404_and_exit () {
    http_response_code(404);
    print('406 citroen not found');
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

include '/wp/inventory/get_wordpress.php';
$wordpress = get_wordpress(
    $_SERVER['WP_ENV'],
    $_SERVER['HTTP_HOST'],
    $_SERVER['DOCUMENT_URI']);
if (! $wordpress) {
    serve_404_and_exit();
}

/** Absolute path to the WordPress directory. */
define('ABSPATH', sprintf('/wp/%s/', $wordpress['wp_version']));

$entrypoint_path = get_wp_entrypoint($wordpress);
if (! $entrypoint_path) {
    serve_go_away_and_exit();
}

include '/wp/credentials/get_db_credentials.php';
setup_db($wordpress);

setup_nonces($wordpress);

enable_wp_debug($wordpress);

/**
 * Define the EPFL_SITE_NAME
 * This match the `site['metadata']['name']` to the 
 * k8s's WordPress object.
 */
define('EPFL_SITE_NAME', $wordpress['site_name']);
// Define the EPFL_WP_UPLOADS constant
$site_upload_dir = '/data/' . EPFL_SITE_NAME . '/uploads';
define('EPFL_SITE_UPLOADS_DIR', $site_upload_dir);

// Initialize WordPress' constants. This is best done using
// `wp-settings.php`, rather than `load.php` and `index.php` which
// both insist on loading a `wp-config.php` file.
settings_before_wp_settings();
require(ABSPATH . 'wp-settings.php');

// @WARNING Because of global variables business, the following needs to happen at the top level — Not in a function!!
require(ABSPATH . $entrypoint_path);
