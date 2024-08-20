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
 * index.php.
 */

function get_wordpress ($wp_env, $host, $uri) {
    // TODO: look these up from a JSON ConfigMap, maintained by the WordPress operator, tabulating all sites
    return array('host'       => 'wp-httpd',
                 'wp_env'     => getenv('WP_ENV'),
                 'wp_version' => '6',
                 'site_uri'   => '/',
                 'wp_debug'   => FALSE);
}

function get_db_credentials ($wordpress) {
    // TODO: look these up from a JSON Secret, maintained by the WordPress operator, tabulating all sites
    return array('db_host' => 'db',
                 'db_name' => 'wp_slky5bbtzy4fojhlw7uiizqcvnn6b',
                 'db_user' => 'eqwc3jfivcsucynj',
                 'db_password' => 'ZKmWc8HoPGEyTW9bjIVQ');
}

function query_looks_bad () {
    return false;  // Nothing to see here. Move along
}

function enable_wp_debug () {
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
    define( 'DB_CHARSET', 'utf8' );
    define( 'DB_COLLATE', '' );
    define( 'DB_HOST', $db_credentials["db_host"]);
    define( 'DB_NAME', $db_credentials["db_name"]);
    define( 'DB_USER', $db_credentials["db_user"]);
    define( 'DB_PASSWORD', $db_credentials["db_password"]);

    global $table_prefix; $table_prefix = "wp_";
}

/**
 * Figure out which PHP file we need to hand over control to
 */
function get_wp_entrypoint () {
    $entrypoint_path = strtok($_SERVER["REQUEST_URI"], '?');
    if ( has_path_traversal($entrypoint_path) ) {
        return null;
    }
    if ( substr($entrypoint_path, -4) === '.php' ) {
        return $entrypoint_path;
    } elseif ( basename($entrypoint_path) === 'wp-admin' ) {
        return 'wp-admin/index.php';
    } else {
        // This catch-all case also includes /wp-json/ etc.
        return 'index.php';
    }
}

function has_path_traversal ($path) {
    if ( substr($path, 1) === '.' ) {
        return true;
    } elseif (false !== strpos($path, '/.')) {
        return true;
    } else {
        return false;
    }
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


##########################################################################################

if (query_looks_bad()) {
    serve_go_away_and_exit();
}

$wordpress = get_wordpress(
    $_SERVER['WP_ENV'],
    $_SERVER['HTTP_HOST'],
    $_SERVER['DOCUMENT_URI']);
if (! $wordpress) {
    serve_404_and_exit();
}

/** Absolute path to the WordPress directory. */
define('ABSPATH', sprintf('/wp/%s/', $wordpress['wp_version']));

$entrypoint_path = get_wp_entrypoint();
if (! $entrypoint_path) {
    serve_go_away_and_exit();
}
setup_db($wordpress);

setup_nonces($wordpress);

enable_wp_debug();

require_once(ABSPATH . 'wp-settings.php');
// @WARNING Because of global variables business, the following needs to happen at the top level — Not in a function!!
require_once(ABSPATH . $entrypoint_path);
