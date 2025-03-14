FROM httpd:2

# Change the default port to 8080
RUN sed -i "s/Listen 80/Listen ${PORT:-8080}/g" /usr/local/apache2/conf/httpd.conf

# Activate the mod_rewrite
RUN sed -i "s/^#LoadModule rewrite_module/LoadModule rewrite_module/" /usr/local/apache2/conf/httpd.conf

# Change DocumentRoot and vhost's Directory to /srv/subdomains
RUN sed -i 's|/usr/local/apache2/htdocs|/srv/subdomains|g' /usr/local/apache2/conf/httpd.conf

# And finally, allow htaccess override
RUN sed -i '/<Directory "\/srv\/subdomains">/,/<\/Directory>/c<Directory /srv/subdomains>\n\tOptions FollowSymLinks\n\tAllowOverride All\n\tRequire all granted\n<\/Directory>' /usr/local/apache2/conf/httpd.conf
