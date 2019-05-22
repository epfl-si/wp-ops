FROM ubuntu:bionic

# Version pins are defined here:
ENV PHP_VERSION=7.3
ARG WORDPRESS_VERSION_LINEAGE=4.9

# Travis-specific arguments — See ../../.travis.yml
ARG GITHUB_API_USER
ARG GITHUB_API_TOKEN
ARG INSTALL_AUTO_FLAGS

ENV DEBIAN_FRONTEND=noninteractive

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
RUN set -x;                                                              \
   curl -o /usr/local/bin/wp -L                                          \
        $(curl $(if [ -n "${GITHUB_API_TOKEN}" ]; then                   \
                echo -u "${GITHUB_API_USER}":"${GITHUB_API_TOKEN}";      \
              fi)                                                        \
        https://api.github.com/repos/wp-cli/wp-cli/releases              \
       | jq -r 'if type == "object" then error                           \
                else [.[] | select (.tag_name | startswith("v1.5"))][0]  \
                          | .assets[0].browser_download_url              \
                end')
RUN chmod 755 /usr/local/bin/wp

# Add Polylang-related extension packages to wp-cli
COPY ./config.yml /var/www/.wp-cli/config.yml
RUN mkdir /var/www/.composer; \
    chown -R www-data:www-data /var/www/.wp-cli /var/www/.composer
RUN su -s /bin/sh www-data -c " \
    set -e -x;                                                            \
    if [ -n '${GITHUB_API_TOKEN}' ]; then                                 \
        composer config -g github-oauth.github.com '${GITHUB_API_TOKEN}'; \
    fi;                                                                   \
    wp package install https://github.com/diggy/polylang-cli.git ;        \
    wp package install https://github.com/cortneyray/wp-cli-polylang.git; \
    rm -f ~/.composer/auth.json"

# Install a copy of WordPress into /wp, populate it with our plugins,
# and patch it to support our symlink-based serving layout
RUN mkdir /wp
RUN wp --allow-root --path=/wp core download \
  --version=$(curl https://api.wordpress.org/core/version-check/1.7/     \
            | jq -r '.offers[].current                                   \
                      | select(match("'${WORDPRESS_VERSION_LINEAGE}'"))' \
            |sort -n -r |head -1)

RUN rm -rf /wp/wp-content/plugins/akismet /wp/wp-content/plugins/hello.php

ADD wordpress-anywhere.patch /tmp/
RUN set -e -x; cd /; git apply < /tmp/wordpress-anywhere.patch;          \
    rm /tmp/wordpress-anywhere.patch

ADD install-plugins-and-themes.py /tmp/
# Get all plugins and themes ("auto" mode) from the jahia2wp manifest:
RUN set -x; /tmp/install-plugins-and-themes.py auto ${INSTALL_AUTO_FLAGS}

######################################################################
# Manually override themes and plugins
######################################################################

# jahia2wp uses an ancient version of Polylang (for reasons that have
# no bearing on the task at hand). Upgrade it:
RUN set -e -x;                                                           \
    cd /wp/wp-content/plugins;                                           \
    rm -rf polylang;                                                     \
    /tmp/install-plugins-and-themes.py polylang wordpress.org/plugins

# Prevent directory listings in the mu-plugins/ subdirectories of sites:
RUN cp /wp/wp-content/plugins/index.php /wp/wp-content/mu-plugins/index.php

# For importing sites from the WXR XML format (e.g. "ventilation" operations)
RUN cd /wp/wp-content/plugins;                                           \
    /tmp/install-plugins-and-themes.py wordpress-importer wordpress.org/plugins

RUN rm -rf /tmp/install-plugins*
