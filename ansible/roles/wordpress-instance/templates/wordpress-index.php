{# WordPress' index.php, with custom tweaks when working in
 # "symlink" mode.
-#}
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
{% if wp_is_symlinked %}
require_once('/wp/wp-blog-header.php');
{% else %}
require( dirname( __FILE__ ) . '/wp-blog-header.php' );
{% endif %}
