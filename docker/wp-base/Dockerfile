FROM ubuntu:bionic

ENV DEBIAN_FRONTEND=noninteractive
ARG PHP_VERSION=7.3
ARG WORDPRESS_VERSION_LINEAGE=4.9

RUN apt-get -qy update && \
    apt-get -qy install curl ca-certificates \
               software-properties-common apt-transport-https gnupg && \
    apt-get -qy autoremove && \
    apt-get clean

RUN curl -sL https://deb.nodesource.com/setup_11.x | bash -

# “The main PPA for supported PHP versions[...]”, see
# https://launchpad.net/~ondrej/+archive/ubuntu/php
RUN add-apt-repository ppa:ondrej/php

RUN apt-get -qy update && apt-get  -qy install --no-install-recommends \
    composer \
    git \
    jq \
    less \
    nodejs \
    php${PHP_VERSION} \
    php${PHP_VERSION}-cli \
    php${PHP_VERSION}-curl \
    php${PHP_VERSION}-gd \
    php${PHP_VERSION}-ldap \
    php${PHP_VERSION}-mbstring \
    php${PHP_VERSION}-mysql \
    php${PHP_VERSION}-xml \
    php${PHP_VERSION}-zip \
    python3-yaml \
    python3-requests \
    unzip \
    vim \
  && \
    apt-get -qy autoremove && \
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

# Install a copy of WordPress into /wp, populate it with our plugins,
# and patch it to support our symlink-based serving layout
RUN mkdir /wp
RUN wp --allow-root --path=/wp core download \
  --version=$(curl https://api.wordpress.org/core/version-check/1.7/   \
            | jq -r '.offers[].current                                 \
                      | select(match("'${WORDPRESS_VERSION_LINEAGE}'"))' \
            |sort -n -r |head -1)

ADD wordpress-anywhere.patch /tmp/
RUN cd /; git apply < /tmp/wordpress-anywhere.patch

ADD install-plugins-and-themes.py /tmp/
RUN python3 /tmp/install-plugins-and-themes.py auto

RUN rm -rf /tmp/install-plugins* /tmp/wordpress-anywhere.patch
