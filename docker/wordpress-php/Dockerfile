FROM ubuntu:jammy

ARG PHP_VERSION=8.2
RUN set -e -x; \
    apt -qy update ; \
    apt -qy install --no-install-recommends \
        msmtp  msmtp-mta software-properties-common gpg-agent ; \
    add-apt-repository ppa:ondrej/php ; \
    apt -qy update ; \
    apt -qy install php${PHP_VERSION}-fpm php${PHP_VERSION}-cli php${PHP_VERSION}-curl php${PHP_VERSION}-gd php${PHP_VERSION}-ldap    \
    php${PHP_VERSION}-mbstring php${PHP_VERSION}-mysql php${PHP_VERSION}-xml php${PHP_VERSION}-zip ;                                                 \
    apt-get -qy autoremove ;                                          \
    apt-get clean

COPY --from=wp-base /wp /wp
COPY --from=wp-base /usr/local/bin/wp /usr/local/bin/wp
COPY --from=wp-base /var/www/.composer/ /var/www/.composer/
COPY --from=wp-base /var/www/.wp-cli/ /var/www/.wp-cli/

COPY msmtprc /etc/msmtprc
RUN sed -i 's|^pid = .*|pid = /run/php-fpm.pid|' /etc/php/${PHP_VERSION}/fpm/php-fpm.conf
RUN sed -i 's|^;log_level = .*|log_level = notice|' /etc/php/${PHP_VERSION}/fpm/php-fpm.conf
RUN sed -i 's|^;log_limit = .*|log_limit = 4096|' /etc/php/${PHP_VERSION}/fpm/php-fpm.conf
RUN sed -i 's|^error_log = .*|error_log = /proc/self/fd/2|' /etc/php/${PHP_VERSION}/fpm/php-fpm.conf

COPY php.ini /etc/php/${PHP_VERSION}/fpm/conf.d/local.ini

RUN sed -i 's|^listen = .*|listen = /run/php-fpm/php-fpm.sock|' /etc/php/${PHP_VERSION}/fpm/pool.d/www.conf
RUN echo "listen.mode = 0666" >> /etc/php/${PHP_VERSION}/fpm/pool.d/www.conf
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
