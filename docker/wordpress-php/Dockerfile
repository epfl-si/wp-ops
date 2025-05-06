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

RUN mkdir -p /wp/nginx-entrypoint/
COPY nginx-entrypoint.php /wp/nginx-entrypoint/nginx-entrypoint.php

# WordPress insists on loading wp-config.php, but in our Web serving
# workflow, all the setup work is handled by nginx-entrypoint.php:
COPY stub-wp-config.php /wp/6/wp-config.php
RUN set -e -x;                                                     \
    for wp in /wp/6*; do                                       \
      if [ ! -f "$wp/wp-config.php" ]; then                        \
        cp /wp/6/wp-config.php "$wp/wp-config.php" ;               \
      fi;                                                          \
    done

EXPOSE 8080 8443

ENTRYPOINT ["bash", "-c", "exec /usr/sbin/php-fpm* -F"]
