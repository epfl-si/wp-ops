FROM docker-registry.default.svc:5000/wwp-test/wp-base

RUN echo "deb http://nginx.org/packages/ubuntu `lsb_release -cs` nginx" > /etc/apt/sources.list.d/nginx.list
RUN curl -fsSL https://nginx.org/keys/nginx_signing.key | apt-key add -

RUN apt-get -qy update && apt-get -qy install --no-install-recommends \
    gettext-base \
    libcgi-pm-perl \
    libio-all-lwp-perl \
    libreadonly-perl \
    msmtp \
    msmtp-mta \
    nginx \
    nginx-module-njs \
    php${PHP_VERSION}-fpm \
  && \
    apt-get -qy autoremove && \
    apt-get clean

COPY msmtprc /etc/msmtprc
RUN sed -i 's|^pid = .*|pid = /run/php-fpm.pid|' /etc/php/${PHP_VERSION}/fpm/php-fpm.conf
RUN sed -i 's|^;log_level = .*|log_level = notice|' /etc/php/${PHP_VERSION}/fpm/php-fpm.conf
RUN sed -i 's|^;log_limit = .*|log_limit = 4096|' /etc/php/${PHP_VERSION}/fpm/php-fpm.conf
RUN sed -i 's|^error_log = .*|error_log = /proc/self/fd/2|' /etc/php/${PHP_VERSION}/fpm/php-fpm.conf

RUN sed -i 's|^listen = .*|listen = /run/php-fpm.sock|' /etc/php/${PHP_VERSION}/fpm/pool.d/www.conf
RUN sed -i 's|;access.log = .*|access.log = /dev/null|' /etc/php/${PHP_VERSION}/fpm/pool.d/www.conf
RUN echo 'catch_workers_output = yes' >> /etc/php/${PHP_VERSION}/fpm/pool.d/www.conf

# directory for custom error pages
RUN mkdir /var/www/global-error
COPY global-error /var/www/global-error

# Band-aid for running WordPress outside of its installation directory
# nginx-entrypoint.php takes care of the setup legwork
RUN set -e -x;                                                     \
    for wp in $(find /wp/ -mindepth 1 -maxdepth 1 -type d          \
                -regextype egrep -regex '.*/[0-9.]+');             \
    do echo "<?php # This wp-config.php intentionally left blank"  \
            > $wp/wp-config.php; done

COPY docker-entrypoint.sh /
RUN chmod a+x /docker-entrypoint.sh

COPY nginx.conf /etc/nginx/nginx.conf
RUN rm /etc/nginx/conf.d/*
COPY conf.d/nginx-wp.conf /etc/nginx/conf.d/nginx-wp.conf

RUN mkdir -p /wp/nginx-entrypoint/
COPY nginx-entrypoint.php /wp/nginx-entrypoint/nginx-entrypoint.php

EXPOSE 8080 8443

ENTRYPOINT ["/docker-entrypoint.sh"]
