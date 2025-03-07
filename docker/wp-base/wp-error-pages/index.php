<?php

// Custom XXX error page.

$statuses = [
  403 => "Forbidden",
  500 => "Internal Server Error",
  502 => "Bad Gateway",
  503 => "Service Unavailable",
  504 => "Gateway Timeout",
];

$status = $_SERVER["STATUS"] ?? 500;
$st = array_key_exists($status, $statuses) ? $status : 500;

header("HTTP/1.1 $st {$statuses[$st]}");

$request_uri = $_SERVER["REQUEST_URI"];
$request_ip  = (array_key_exists("HTTP_CF_CONNECTING_IP", $_SERVER)) ? $_SERVER["HTTP_CF_CONNECTING_IP"] : $_SERVER["REMOTE_ADDR"];

// ip protocol version & regex to check if inside EPFL campus
$ip_v = "IPv4";
$ip_regex = "/^128\.17(8|9)/";

if (filter_var($request_ip, FILTER_VALIDATE_IP, FILTER_FLAG_IPV6)) {
  $ip_v = "IPv6";
  $ip_regex = "/^2001:620:618:/";
}

// is the requested page the login or wp-admin?
$is_login = strpos($request_uri, "wp-login") !== false;
$is_wp_admin = strpos($request_uri, "wp-admin") !== false;

$is_inside_epfl = preg_match($ip_regex, $request_ip) == 1;
$is_inside_epfl_string = $is_inside_epfl ? "inside EPFL" : "outside EPFL";

$error_types = ["default", "accred", "inside"];
$error_type = "default";

if (array_key_exists("error_type", $_GET) && in_array($_GET["error_type"], $error_types)) {
  $error_type = $_GET["error_type"];
}

$stx = $st == 403 ? "403" : "50x";

include("{$stx}-template.php");
