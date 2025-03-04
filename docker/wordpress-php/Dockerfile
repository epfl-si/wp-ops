FROM ubuntu:jammy

ARG PHP_VERSION=8.2
RUN set -e -x; \
    apt -qy update ; \
    apt -qy install --no-install-recommends \
        msmtp  msmtp-mta software-properties-common gpg-agent ; \
    add-apt-repository ppa:ondrej/php ; \
    apt -qy update ; \
    bash -c 'apt -qy install php${PHP_VERSION}-{fpm,cli,curl,gd,ldap,mbstring,mysql,xml,zip}' ; \
    apt-get -qy autoremove ; \
    apt-get clean

COPY --from=wp-base /wp /wp
COPY --from=wp-base /usr/local/bin/wp /usr/local/bin/wp
COPY --from=wp-base /var/www/.composer/ /var/www/.composer/
COPY --from=wp-base /var/www/.wp-cli/ /var/www/.wp-cli/

# We don't do the wp-cron out of the interactive Web server:
RUN find /wp/ -name wp-cron.php -delete

COPY msmtprc /etc/msmtprc

COPY merge_fpm_confs.pl /usr/local/lib/
COPY php-fpm.conf.overrides /etc/php/${PHP_VERSION}/fpm/
COPY www.conf.overrides /etc/php/${PHP_VERSION}/fpm/pool.d/

RUN set -e -x; \
    cd /etc/php/${PHP_VERSION}/fpm/; \
    mv php-fpm.conf php-fpm.conf.orig; \
    perl /usr/local/lib/merge_fpm_confs.pl php-fpm.conf.orig php-fpm.conf.overrides > php-fpm.conf; \
    cd pool.d; \
    mv www.conf www.conf.orig; \
    perl /usr/local/lib/merge_fpm_confs.pl www.conf.orig www.conf.overrides > www.conf; \
    rm /usr/local/lib/merge_fpm_confs.pl

COPY php.ini /etc/php/${PHP_VERSION}/fpm/conf.d/local.ini

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
