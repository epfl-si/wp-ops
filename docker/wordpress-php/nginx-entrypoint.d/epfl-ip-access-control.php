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

if  (( isset($_SERVER['HTTP_X_EPFL_INTERNAL']) && strtoupper($_SERVER['HTTP_X_EPFL_INTERNAL']) != 'TRUE') 
    && ( strpos($entrypoint_path, 'wp-admin') !== false || $_SERVER['HTTP_HOST'] === 'inside.epfl.ch' ))
{
    header('Location: https://www.epfl.ch/campus/services/en/vpn-error/', true, 302);
    exit();
}
