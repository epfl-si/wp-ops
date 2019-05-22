# A library of reusable shell functions for maintenance mode

enter_maintenance_mode() {
    local htaccess htaccesstmp
    htaccess="{{ wp_dir }}"/.htaccess
    htaccesstmp="$htaccess"_tmp_$$
    (echo "RewriteRule .* /global-error/303-to-sorryserver.php [L]";
     grep -v /303-to-sorryserver.php "$htaccess" || true) > "$htaccesstmp"
    mv "$htaccesstmp" "$htaccess"
}

leave_maintenance_mode() {
    local htaccess htaccesstmp
    htaccess="{{ wp_dir }}"/.htaccess
    htaccesstmp="$htaccess"_tmp_$$
    grep -v /303-to-sorryserver.php "$htaccess" > "$htaccesstmp"
    mv "$htaccesstmp" "$htaccess"
}
