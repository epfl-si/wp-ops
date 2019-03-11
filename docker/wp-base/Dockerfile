FROM ubuntu:bionic

ENV DEBIAN_FRONTEND=noninteractive
ENV PHP_VERSION=7.3

RUN apt-get -y update && \
    apt-get -y install curl ca-certificates \
               software-properties-common apt-transport-https gnupg && \
    apt-get -y autoremove && \
    apt-get clean

RUN curl -sL https://deb.nodesource.com/setup_11.x | bash -
RUN add-apt-repository ppa:ondrej/php
RUN apt-get -y update && apt-get  -y install --no-install-recommends \
    composer \
    git \
    jq \
    less \
    nodejs \
    php${PHP_VERSION} \
    php${PHP_VERSION}-apcu \
    php${PHP_VERSION}-cli \
    php${PHP_VERSION}-curl \
    php${PHP_VERSION}-gd \
    php${PHP_VERSION}-ldap \
    php${PHP_VERSION}-mysql \
    php${PHP_VERSION}-xml \
    php${PHP_VERSION}-zip \
    unzip \
    vim \
  && \
    apt-get -y autoremove && \
    apt-get clean

# Download latest WP-CLI in the 1.5.x branch (otherwise diggy/polylang-cli
# won't install):
RUN curl -o /usr/local/bin/wp -L `curl https://api.github.com/repos/wp-cli/wp-cli/releases | jq -r '[.[] | select (.tag_name | startswith("v1.5"))][0] | .assets[0].browser_download_url'`
RUN chmod 755 /usr/local/bin/wp

# Add Polylang-related extension packages to wp-cli
COPY ./config.yml /var/www/.wp-cli/config.yml
RUN chown -R www-data:www-data /var/www/.wp-cli
RUN su -s /bin/sh www-data -c "wp package install https://github.com/diggy/polylang-cli.git"
RUN su -s /bin/sh www-data -c "wp package install https://github.com/cortneyray/wp-cli-polylang.git"

# Install a copy of WordPress into /wp and populate it with our plugins
RUN mkdir /wp
RUN wp --allow-root --path=/wp core download
ADD plugins.csv install-plugins.sh /tmp/
RUN sh /tmp/install-plugins.sh < /tmp/plugins.csv; \
        rm /tmp/install-plugins.sh /tmp/plugins.csv
