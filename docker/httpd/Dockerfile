FROM epflidevelop/os-wp-base

RUN apt-get update && apt-get install -y --no-install-recommends \
    apache2 \
    libapache2-mod-php${PHP_VERSION} \
    libcgi-pm-perl \
    libio-all-lwp-perl \
    libreadonly-perl \
    vim \
  && \
    apt-get -y autoremove && \
    apt-get clean

COPY php.ini /etc/php/95-epfl.ini
RUN mv /etc/php/95-epfl.ini /etc/php/${PHP_VERSION}/apache2/conf.d

RUN a2dismod mpm_event mpm_worker
RUN a2enmod mpm_prefork php${PHP_VERSION} cgi

# directory for custom error pages
RUN mkdir /var/www/error

COPY apache2.conf /etc/apache2/
COPY ports.conf /etc/apache2/
COPY error-pages.conf /etc/apache2/conf-enabled/
COPY 403 /var/www/error/
COPY docker-entrypoint.sh /
COPY health.cgi /usr/lib/cgi-bin
RUN chmod a+x /docker-entrypoint.sh /usr/lib/cgi-bin/health.cgi

EXPOSE 8080 8443

ENTRYPOINT ["/docker-entrypoint.sh"]

