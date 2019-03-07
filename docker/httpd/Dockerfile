FROM epflidevelop/os-wp-base

RUN apt-get update && apt-get install -y --no-install-recommends \
    apache2 \
    libapache2-mod-php7.3 \
    libcgi-pm-perl \
    libio-all-lwp-perl \
    libreadonly-perl \
    vim \
  && \
    apt-get -y autoremove && \
    apt-get clean

COPY php.ini /etc/php/7.3/apache2/conf.d/95-epfl.ini

RUN a2dismod mpm_event mpm_worker
RUN a2enmod mpm_prefork php7.3 cgi

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

