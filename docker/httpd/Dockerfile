FROM ubuntu:bionic

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    apache2 \
    curl \
    ca-certificates \
    libapache2-mod-security2 \
    lsb-release \
    apt-transport-https \
    libcgi-pm-perl \
    libio-all-lwp-perl \
    libreadonly-perl \
    vim \
  && \
    apt-get -y autoremove && \
    apt-get clean

# The following goodies have dependencies above this line, and
# thus must be installed in another round of apt-get
RUN  apt-get -y update && \
  apt-get -y install nodejs \
    libapache2-mod-php7.2 \
    php7.2 \
    php7.2-gd \
    php7.2-cli \
    php7.2-curl \
    php7.2-ldap \
    php7.2-mysql \
    php7.2-xml \
    php7.2-zip \
    php7.2-apcu \
    php7.2-mbstring \
    lttng-tools \
  && \
    apt-get -y autoremove && \
    apt-get clean

# See https://github.com/naser/LTTng-enabled-PHP
# Also, https://github.com/openshift/origin/issues/19198 says we
# cannot use multi-stage builds yet.
RUN BUILDDEPS='php7.2-dev build-essential git liblttng-ust-dev' ;\
   set -e -x; apt-get -y install $BUILDDEPS ; \
    mkdir /build; cd /build; \
    git clone https://github.com/naser/LTTng-php-tracing-module.git ; \
    cd /build/LTTng-php-tracing-module; \
    phpize; ./configure; make; make install; \
    echo '; extension=lttng.so' > /etc/php/7.2/cli/conf.d/90-curl.ini; \
    rm -rf /build; \
    apt-get remove -y --purge $BUILDDEPS; \
    apt-get autoremove -y --purge; apt-get clean

COPY php.ini /etc/php/7.2/apache2/conf.d/95-epfl.ini

RUN a2enmod cgi

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

