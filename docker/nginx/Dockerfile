FROM docker-registry.default.svc:5000/wwp-test/wp-base

RUN set -e -x; \
    apt-get -qy update && apt-get -qy install --no-install-recommends \
    msmtp \
    msmtp-mta \
    php${PHP_VERSION}-fpm ; \
    apt-get -qy autoremove ; \
    apt-get clean

COPY msmtprc /etc/msmtprc
RUN sed -i 's|^pid = .*|pid = /run/php-fpm.pid|' /etc/php/${PHP_VERSION}/fpm/php-fpm.conf
RUN sed -i 's|^;log_level = .*|log_level = notice|' /etc/php/${PHP_VERSION}/fpm/php-fpm.conf
RUN sed -i 's|^;log_limit = .*|log_limit = 4096|' /etc/php/${PHP_VERSION}/fpm/php-fpm.conf
RUN sed -i 's|^error_log = .*|error_log = /proc/self/fd/2|' /etc/php/${PHP_VERSION}/fpm/php-fpm.conf

COPY php.ini /etc/php/${PHP_VERSION}/fpm/conf.d/local.ini

RUN sed -i 's|^listen = .*|listen = /run/php-fpm/php-fpm.sock|' /etc/php/${PHP_VERSION}/fpm/pool.d/www.conf
RUN sed -i 's|;access.log = .*|access.log = /dev/null|' /etc/php/${PHP_VERSION}/fpm/pool.d/www.conf
RUN echo 'catch_workers_output = yes' >> /etc/php/${PHP_VERSION}/fpm/pool.d/www.conf

# Band-aid for running WordPress outside of its installation directory
# nginx-entrypoint.php takes care of the setup legwork
RUN set -e -x;                                                     \
    for wp in $(find /wp/ -mindepth 1 -maxdepth 1 -type d          \
                -regextype egrep -regex '.*/[0-9.]+');             \
    do echo "<?php # This wp-config.php intentionally left blank"  \
            > $wp/wp-config.php; done

RUN mkdir -p /wp/nginx-entrypoint/
COPY nginx-entrypoint.php /wp/nginx-entrypoint/nginx-entrypoint.php

EXPOSE 8080 8443

ENTRYPOINT ["bash", "-c", "exec /usr/sbin/php-fpm* -F"]
