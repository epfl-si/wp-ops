<?php

  // Custom 403 error page.
  //
  // This script finds the error type (e.g. "default")
  // and then includes 403-template.php which in turn includes
  // 403-{$error_type}.php.

  // make sure we send a 403 status code
  header("HTTP/1.1 403 Forbidden");

  // request variables
  $request_id  = $_SERVER["UNIQUE_ID"] ?? '';
  $request_uri = $_SERVER["REQUEST_URI"];
  // If using CloudFlare, we retrieve original client IP in 'HTTP_CF_CONNECTING_IP'. The content of 'REMOTE_ADDR' is a CloudFlare IP.
  $request_ip  = (array_key_exists("HTTP_CF_CONNECTING_IP", $_SERVER)) ? $_SERVER["HTTP_CF_CONNECTING_IP"] : $_SERVER["REMOTE_ADDR"];

  // ip protocol version & regex to check if inside EPFL campus
  $ip_v = "IPv4";
  $ip_regex = "/^128\.17(8|9)/";

  if (filter_var($request_ip, FILTER_VALIDATE_IP, FILTER_FLAG_IPV6))
  {
    $ip_v = "IPv6";
    $ip_regex = "/^2001:620:618:/";
  }

  // is the requested page the login or wp-admin?
  $is_login = strpos($request_uri, "wp-login") !== false;
  $is_wp_admin = strpos($request_uri, "wp-admin") !== false;

  // is the user's IP inside the EPFL campus?
  $is_inside_epfl = preg_match($ip_regex, $request_ip) == 1;
  $is_inside_epfl_string = $is_inside_epfl ? "inside EPFL" : "outside EPFL";

  // the error types supported by this page
  $error_types = ["default", "accred", "inside"];

  // the current error type
  $error_type = "default";


  // the error type can be overridden by a GET parameter,
  // this is useful for testing and it's used for the
  // accred error, because it comes from a redirect. We
  // check that's is a supported error:
  if (array_key_exists("error_type", $_GET) && in_array($_GET["error_type"], $error_types))
  {
    $error_type = $_GET["error_type"];
  }

  include ("403-template.php");
?>
