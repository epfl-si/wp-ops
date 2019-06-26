#!/bin/sh

set -e

cat > /etc/apache2/conf-available/dyn-vhost.conf <<EOF
UseCanonicalName Off

RemoteIPHeader X-Forwarded-For
RemoteIPInternalProxy 172.31.0.0/16 10.180.21.0/24 127.0.0.0/8

LogFormat "%V %a %l %u %t \"%r\" %>s %b \"%{Referer}i\" \"%{User-agent}i\" \"%{X-EPFL-Trace-Id}i\" %{CF-Connecting-IP}i %T %D" vcommon
CustomLog "| /usr/bin/rotatelogs /srv/${WP_ENV}/logs/access_log.$(hostname).%Y%m%d 86400" vcommon
CustomLog "/dev/stdout" vcommon

ErrorLog "| /usr/bin/rotatelogs /srv/${WP_ENV}/logs/error_log.$(hostname).%Y%m%d 86400"

VirtualDocumentRoot "/srv/${WP_ENV}/%0/htdocs"

<VirtualHost *:8443>
  SSLEngine on
  SSLCertificateFile "/etc/apache2/ssl/server.cert"
  SSLCertificateKeyFile "/etc/apache2/ssl/server.key"
</VirtualHost>

<VirtualHost *:9980>
  VirtualDocumentRoot "/srv/${WP_ENV}/${WP_ENV}-metrics/htdocs"
  ProxyPreserveHost On
</VirtualHost>
EOF

# Directory to log web services calls and generic logs. It may already exists if we're on Openshift
LOG_FOLDER="/call_logs"
if [ ! -d $LOG_FOLDER ]
then
    /bin/mkdir -p $LOG_FOLDER
    /bin/chown www-data: $LOG_FOLDER
fi

/bin/mkdir -p /srv/${WP_ENV}/logs
/bin/mkdir -p /srv/${WP_ENV}/jahia2wp

/bin/chown www-data: /srv/${WP_ENV}
/bin/chown www-data: /srv/${WP_ENV}/logs
/bin/chown www-data: /srv/${WP_ENV}/jahia2wp

/bin/mkdir -p /etc/apache2/ssl
if ! [ -f /etc/apache2/ssl/server.key -a -f /etc/apache2/ssl/server.cert ]; then
    /usr/bin/openssl req -x509 -sha256 -nodes -days 3650 -newkey rsa:4096 -keyout /etc/apache2/ssl/server.key -out /etc/apache2/ssl/server.cert -subj "/C=CH/ST=Vaud/L=Lausanne/O=Ecole Polytechnique Federale de Lausanne (EPFL)/CN=*.epfl.ch"
fi

/bin/mkdir -p /var/www/html/probes/ready
echo "OK" > /var/www/html/probes/ready/index.html

set -x
# Change max upload size for http requests
sed -i "s/upload_max_filesize = .*/upload_max_filesize = 300M/" /etc/php/${PHP_VERSION}/apache2/php.ini
sed -i "s/post_max_size = .*/post_max_size = 300M/" /etc/php/${PHP_VERSION}/apache2/php.ini
# Change max upload size for CLI requests
sed -i "s/upload_max_filesize = .*/upload_max_filesize = 300M/" /etc/php/${PHP_VERSION}/cli/php.ini
sed -i "s/post_max_size = .*/post_max_size = 300M/" /etc/php/${PHP_VERSION}/cli/php.ini

/usr/sbin/a2dissite 000-default
/usr/sbin/a2enmod ssl
/usr/sbin/a2enmod rewrite
/usr/sbin/a2enmod vhost_alias
/usr/sbin/a2enmod proxy
/usr/sbin/a2enmod proxy_http
/usr/sbin/a2enmod headers
/usr/sbin/a2enmod status
/usr/sbin/a2enmod remoteip
/usr/sbin/a2enconf dyn-vhost

/usr/sbin/apache2ctl -DFOREGROUND
