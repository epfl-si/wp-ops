<?php

/**
 * EPFL nginx entrypoint extension: reject traffic from outside the internal network in some cases.
 *
 * The `X-EPFL-Internal` request header is set by our reverse proxies
 * (AVI loadbalancer), and is therefore trusted. Reject attempts to
 * browse at `/wp-admin/` (regardless of hostname) and
 * `inside.epfl.ch` (regardless of path), except if that header is
 * set to `TRUE`.
 */

namespace EPFL\RequestFiltering;

function is_permitted_traffic ($entrypoint_path) {
    if (! isset($_SERVER['HTTP_X_EPFL_INTERNAL'])) {
        return true;    // Development
    } else if ($_SERVER['HTTP_X_EPFL_INTERNAL'] == 'TRUE') {
        return true;    // Allow everyting from inside EPFL
    } else if ($_SERVER['HTTP_HOST'] === 'inside.epfl.ch') {
        return false;
    } else if (strpos($entrypoint_path, 'wp-admin') !== false) {
        return false;   // No approaching the back-office from outside; use VPN
    } else {
        return true;
    }
}

if (! is_permitted_traffic($entrypoint_path)) {
    header('Location: https://www.epfl.ch/campus/services/en/vpn-error/', true, 302);
    exit();
}
