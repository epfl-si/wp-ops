FROM docker-registry.default.svc:5000/wwp-test/wp-base

RUN apt-get -qy update && apt-get -qy install --no-install-recommends \
    gettext-base \
    libcgi-pm-perl \
    libio-all-lwp-perl \
    libreadonly-perl \
    msmtp \
    msmtp-mta \
    nginx \
    php${PHP_VERSION}-fpm \
  && \
    apt-get -qy autoremove && \
    apt-get clean

COPY msmtprc /etc/msmtprc
COPY php.ini /etc/php/95-epfl.ini
RUN mv /etc/php/95-epfl.ini /etc/php/${PHP_VERSION}/apache2/conf.d
RUN sed -i 's|^pid = .*|pid = /run/php-fpm.pid|' /etc/php/${PHP_VERSION}/fpm/php-fpm.conf
RUN sed -i 's|^listen = .*|listen = /run/php-fpm.sock|' /etc/php/${PHP_VERSION}/fpm/pool.d/www.conf

COPY docker-entrypoint.sh /
RUN chmod a+x /docker-entrypoint.sh

COPY nginx.conf /etc/nginx/nginx.conf.tmpl

EXPOSE 8080 8443

ENTRYPOINT ["/docker-entrypoint.sh"]

