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

// Found in WPForms' assets/pro/js/frontend/fields/file-upload.es5.js
// 💡 There is a more comprehensive list for the server side in
// includes/functions/checks.php but ① it is in a private variable,
// and ② it contains things that we do not use.
function ajax_actions_whitelist () {
    return [
        "wpforms_file_upload_speed_test",
        "wpforms_upload_chunk_init",
        "wpforms_upload_chunk",
        "wpforms_file_chunks_uploaded",
        "wpforms_remove_file",
        "wpforms_submit"
    ];
}

function is_permitted_traffic ($entrypoint_path) {
    if (! isset($_SERVER['HTTP_X_EPFL_INTERNAL'])) {
        return true;    // Development
    } else if ($_SERVER['HTTP_X_EPFL_INTERNAL'] == 'TRUE') {
        return true;    // Allow everyting from inside EPFL
    } else if ($_SERVER['HTTP_HOST'] === 'inside.epfl.ch') {
        return false;
    } else if (strpos($entrypoint_path, 'wp-admin') !== false) {
        if ( (strpos($entrypoint_path, 'wp-admin/admin-ajax.php') !== false) &&
             in_array($_POST["action"], ajax_actions_whitelist()) ) {
            return true;    // Uploads, WPForms submissions etc. still permitted
        } else {
            return false;   // No approaching the back-office from outside; use VPN
        }
    } else {
        return true;
    }
}

if (! is_permitted_traffic($entrypoint_path)) {
    header('Location: https://www.epfl.ch/campus/services/en/vpn-error/', true, 302);
    exit();
}
