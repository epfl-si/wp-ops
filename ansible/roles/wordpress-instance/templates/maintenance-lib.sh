# A library of reusable shell functions for maintenance mode

enter_maintenance_mode() {
    local htaccess htaccesstmp

    htaccess="{{ wp_dir }}"/.htaccess
    cp --backup=numbered "$htaccess" "$htaccess.bak"

    htaccesstmp="$htaccess"_tmp_$$
    cat > "$htaccesstmp" <<HTACCESS_MAINTENANCE
RewriteRule .* /global-error/303-to-sorryserver.php [L]
HTACCESS_MAINTENANCE
    mv "$htaccesstmp" "$htaccess"
}

leave_maintenance_mode() {
    local htaccess

    htaccess="{{ wp_dir }}"/.htaccess
    mv "$htaccess.bak" "$htaccess"
}
