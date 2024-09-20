FROM docker-registry.default.svc:5000/wwp-test/wp-base

RUN perl -i -pe 's/^# deb-src/deb-src/' /etc/apt/sources.list /etc/apt/sources.list.d/*.list

RUN apt -qy update && apt -qy install build-essential dpkg-dev debhelper wget && apt -qy build-dep msmtp

ARG msmtp_url_base=https://launchpad.net/ubuntu/+archive/primary/+sourcefiles/msmtp/1.8.11-2/msmtp_1.8.11
ARG msmtp_patchlevel=2

RUN set -e -x; mkdir /build; cd /build;                                     \
    wget ${msmtp_url_base}-${msmtp_patchlevel}.dsc;                         \
    wget ${msmtp_url_base}.orig.tar.xz;                                     \
    wget ${msmtp_url_base}-${msmtp_patchlevel}.debian.tar.xz;               \
    dpkg-source -x $(basename "${msmtp_url_base}")-${msmtp_patchlevel}.dsc

COPY log-to-stderr.patch /build/

RUN set -e -x; cd /build/msmtp*;                         \
    cp /build/log-to-stderr.patch debian/patches/;       \
    echo log-to-stderr.patch >> debian/patches/series;   \
    dpkg-buildpackage -d;                                \
    mkdir /deb; mv ../*.deb /deb

FROM docker-registry.default.svc:5000/wwp-test/wp-base

RUN apt-get -qy update && apt-get -qy install --no-install-recommends \
    apache2 \
    libapache2-mod-php${PHP_VERSION} \
    php${PHP_VERSION}-apcu \
    libcgi-pm-perl \
    libio-all-lwp-perl \
    libreadonly-perl \
    libsecret-1-0 \
    `case "$(arch)" in x86_64) echo libgsasl18 ;; *) echo libgsasl7 ;; esac` \
  && \
    apt-get -qy autoremove && \
    apt-get clean

COPY --from=0 /deb/ /usr/local/msmtp/
RUN dpkg -i /usr/local/msmtp/*

COPY msmtprc /etc/msmtprc
COPY php.ini /etc/php/95-epfl.ini
RUN mv /etc/php/95-epfl.ini /etc/php/${PHP_VERSION}/apache2/conf.d

RUN a2dismod mpm_event mpm_worker
RUN a2enmod mpm_prefork php${PHP_VERSION} cgi

# directory for custom error pages
RUN mkdir /var/www/global-error

COPY apache2.conf /etc/apache2/
COPY dyn-vhost.conf /etc/apache2/conf-available/
COPY ports.conf /etc/apache2/
COPY error-pages.conf /etc/apache2/conf-enabled/
COPY global-error /var/www/global-error
COPY docker-entrypoint.sh /
COPY health.cgi /usr/lib/cgi-bin
RUN chmod a+x /docker-entrypoint.sh /usr/lib/cgi-bin/health.cgi

EXPOSE 8080 8443

ENTRYPOINT ["/docker-entrypoint.sh"]
