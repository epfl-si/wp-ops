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
    return array("host"    => "wp-httpd",
                 "wp_env"  => getenv("WP_ENV"),
                 "wp_version" => "5",
                 "site_uri" => '/',
                 "wp_debug" => FALSE);
}

function get_db_credentials ($site) {
    // TODO: look these up from a JSON Secret, maintained by the WordPress operator, tabulating all sites
  return array("db_host" => "db",
               "db_name" => 'wp_suifar11gce97j1vaqi9z0srqkw7b',
               "db_user" => 'o9askjsukww3zj5a',
               "db_password" => 'WI2Ly2k3ugFAGwLaOuUs');
}

function query_looks_bad () {
    return false;  // Nothing to see here. Move along
}

function run_wordpress ($site, $db_credentials) {
    define( 'DB_CHARSET', 'utf8' );
    define( 'DB_COLLATE', '' );
    define( 'DB_HOST', $db_credentials["db_host"]);
    define( 'DB_NAME', $db_credentials["db_name"]);
    define( 'DB_USER', $db_credentials["db_user"]);
    define( 'DB_PASSWORD', $db_credentials["db_password"]);

    // TODO: Read these up from another JSON Secret
    define( 'AUTH_KEY',         '_#yH+/R.)X%;`*(4u=gy|Jo5`d8Gj)/1FaU[haP9P$48;v]1Eg7&zk:]nspMKuA#' );
    define( 'SECURE_AUTH_KEY',  'c&%V:8FXis7@;>l+2+FSUGYS?wG01r@W?&jq!V0-z:79A_W{*5CfSYf5{F&3FR!a' );
    define( 'LOGGED_IN_KEY',    'R@d4lS~LwB+:z$n{WN]#K:im_)7DT/~zhQw3S, YSTsl,-?k4/i_<t}rk*Dg) CI' );
    define( 'NONCE_KEY',        'RB~Xw1<TjGLru*w>PC2-fl1h .8>aY|9sa8x7-tm7]Psh{XY!I?Te<_b@qUQ=:mO' );
    define( 'AUTH_SALT',        'pj;f>C9/>dI|978`z@bI)}eb$2~3/:P<g~wd3k%=tbp-O`![td}6z{<{~L73=Fw2' );
    define( 'SECURE_AUTH_SALT', 'p|8ugKn38lKR0/XSt(LaR;}[Rsr}8,|b|BFG^_`N^BHGV?8N{O3d9XH~v5FYHl}i' );
    define( 'LOGGED_IN_SALT',   '{2Y,4WGBE6wT$gdOD.n)duoV5:Jm5d?L@p{`,^HorJ5`>zaprEqc;<]W|d7-T?zE' );
    define( 'NONCE_SALT',       'mVSh!um&7*qGB%sZ,gg6KDD!ko<s,e1Dj>X[CP+fR6<f(&iy[#?~y VBuS^${/&Q' );

    define('ABSPATH', sprintf("/wp/%s/", $site["wp_version"]));
    $_SERVER["SCRIPT_NAME"] = ABSPATH . "index.php";
    include(ABSPATH . "wp-settings.php");
    include($_SERVER["SCRIPT_NAME"]);
}

$wordpress = get_wordpress(
    $_SERVER["WP_ENV"],
    $_SERVER["HTTP_HOST"],
    $_SERVER['DOCUMENT_URI']);
$db_credentials = get_db_credentials($wordpress);

if ($wordpress) {
    if (query_looks_bad()) {
        http_response_code(429, "Go away");
        exit();
    }
    run_wordpress($wordpress, $db_credentials);
} else {
   http_response_code(404);
   print("404 citroen not found");
   
}
