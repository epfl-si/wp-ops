FROM ubuntu:bionic

# Version pins are defined here:
ENV PHP_VERSION=7.3

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get -qy update && \
    apt-get -qy install curl ca-certificates \
               software-properties-common apt-transport-https gnupg && \
    apt-get -qy autoremove && \
    apt-get clean

RUN curl -sL https://deb.nodesource.com/setup_11.x | bash -

# “The main PPA for supported PHP versions[...]”, see
# https://launchpad.net/~ondrej/+archive/ubuntu/php
RUN add-apt-repository ppa:ondrej/php; rm -rf /tmp/tmp*

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


######################################################################
# Install wp-cli
######################################################################

# Travis-specific arguments — See ../../.travis.yml
ARG GITHUB_API_USER
ARG GITHUB_API_TOKEN

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
    wp package install https://github.com/epfl-idevelop/wp-cli.git;       \
    rm -f ~/.composer/auth.json"

######################################################################
# Install and patch WordPresses
######################################################################
# Install multiple versions of WordPress into /wp/, and patch them to
# support our symlink-based serving layout
ARG WORDPRESS_VERSION_LINEAGES="4.9 5.2 5.3"
RUN set -x;                                                              \
    for lineage in ${WORDPRESS_VERSION_LINEAGES}; do                     \
        version=$(curl https://api.wordpress.org/core/version-check/1.7/ \
            | jq -r '.offers[].current                                   \
                      | select(match("'${lineage}'"))'                   \
            |sort -n -r |head -1) ;                                      \
        mkdir -p /wp/$version ;                                          \
        wp --allow-root --path=/wp/$version                              \
           core download --version=$version ;                            \
    done

RUN rm -rf /wp/*/wp-content/plugins/akismet                              \
          /wp/*/wp-content/plugins/hello.php                             \
    /wp/*/wp-content/themes/twenty*

ADD wordpress-anywhere.patch /tmp/
RUN set -e -x;                                                           \
    apt -qy install patch;                                               \
    for wp in /wp/*; do                                                  \
        cd $wp ;                                                         \
        patch -p0 -F3 < /tmp/wordpress-anywhere.patch;                   \
    done;                                                                \
    apt -qy remove --purge patch;                                        \
    rm /tmp/wordpress-anywhere.patch

######################################################################
# Install and patch plugins and themes
######################################################################

ADD install-plugins-and-themes.py clearstatcache-wp-import.patch /tmp/
# Get all plugins and themes ("auto" mode) from the jahia2wp manifest;
ARG INSTALL_AUTO_FLAGS
RUN set -e -x; for wp in /wp/*; do cd $wp ;                              \
        /tmp/install-plugins-and-themes.py auto ${INSTALL_AUTO_FLAGS};   \
    done

# Manually add the wordpress-importer plugin, used in "ventilation"
# operations. Patch it to nuke the stat() cache inbetween downloading
# things
RUN set -e -x; for wp in /wp/*; do                                       \
        cd $wp/wp-content/plugins ;                                      \
        /tmp/install-plugins-and-themes.py                               \
            wordpress-importer wordpress.org/plugins ;                   \
        cd wordpress-importer ;                                          \
        git apply < /tmp/clearstatcache-wp-import.patch ;                \
    done;                                                                \
    rm /tmp/clearstatcache-wp-import.patch

RUN rm /tmp/install-plugins-and-themes.py

# Prevent directory listings in the mu-plugins/ subdirectories of sites:
RUN set -e -x; for wp in /wp/*; do                                       \
        cd $wp/wp-content ;                                              \
        cp plugins/index.php mu-plugins/index.php ;                      \
    done

######################################################################
# Symlinks in /wp
######################################################################
# We do that last for simplicity, at a small cost in build time
COPY symlink-wp-versions.sh /tmp
RUN sh /tmp/symlink-wp-versions.sh && rm /tmp/symlink-wp-versions.sh
