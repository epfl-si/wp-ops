FROM ubuntu:focal

# Version pins are defined here:
ENV PHP_VERSION=7.4
ENV NODE_VERSION_MAJOR=20

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get -qy update && \
    apt-get -qy install ca-certificates \
               software-properties-common apt-transport-https gnupg awscli && \
    apt-get -qy autoremove && \
    apt-get clean

# https://github.com/curl/curl/issues/3750
RUN set -e -x; add-apt-repository ppa:savoury1/curl34; \
  apt-get -qy update; apt-get -qy install curl

RUN mkdir -p /etc/apt/keyrings
RUN curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg
RUN echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_$NODE_VERSION_MAJOR.x nodistro main" > /etc/apt/sources.list.d/nodesource.list

RUN apt-get -qy update && apt-get  -qy install --no-install-recommends \
    bash-completion \
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

# Download latest WP-CLI:
RUN curl -o /usr/local/bin/wp https://raw.githubusercontent.com/wp-cli/builds/gh-pages/phar/wp-cli.phar
RUN chmod 755 /usr/local/bin/wp

# Add Polylang-related extension packages to wp-cli
COPY ./wp-cli-config.yml /var/www/.wp-cli/config.yml
RUN mkdir /var/www/.composer; \
    chown -R www-data:www-data /var/www/.wp-cli /var/www/.composer
RUN su -s /bin/sh www-data -c " \
    set -e -x;                                                            \
    if [ -n '${GITHUB_API_TOKEN}' ]; then                                 \
        composer config -g github-oauth.github.com '${GITHUB_API_TOKEN}'; \
    fi;                                                                   \
    wp package install https://github.com/epfl-si/polylang-cli/archive/master.zip ;     \
    wp package install https://github.com/epfl-si/wp-cli/archive/master.zip;            \
    rm -f ~/.composer/auth.json"

# Make symlinks under /var/www/.wp-cli relative (so that the
# wp-ansible-runner image may safely move that directory to /home/runner):
RUN set -e -x; cd /var/www/.wp-cli; find . -type l | while read l; do     \
        target="$(realpath "$l")";                                        \
        rel="$(realpath --relative-to="$(dirname "$(realpath -s "$l")")"  \
                        "$target")";                                      \
        rm "$l"; ln -s "$rel" "$l";                                       \
    done

######################################################################
# Install and patch WordPresses
######################################################################
# Install multiple versions of WordPress into /wp/, and patch them to
# support our symlink-based serving layout
ARG WORDPRESS_VERSION_LINEAGES="5.5 6.1"
RUN set -e -x;                                                           \
    for lineage in ${WORDPRESS_VERSION_LINEAGES}; do                     \
        version=$(curl http://api.wordpress.org/core/stable-check/1.0/   \
            | jq -r 'keys[]                                              \
                      | select(match("^'${lineage}'"))'                  \
            |sort -n -r |head -1) ;                                      \
        mkdir -p /wp/$version ;                                          \
        wp --allow-root --path=/wp/$version                              \
           core download --version=$version ;                            \
    done

RUN rm -rf /wp/*/wp-content/plugins/akismet                              \
          /wp/*/wp-content/plugins/hello.php                             \
    /wp/*/wp-content/themes/twenty*                                      \
    /wp/*/setup-config.php /wp/*/wp-activate.php                         \
    /wp/*/wp-config-sample.php

ADD wordpress-anywhere.patch.5.5 /tmp/
ADD wordpress-anywhere.patch.5.8 /tmp/
## this one fix https://core.trac.wordpress.org/ticket/57995
## please remove after the wordpress core is updated
ADD wordpress-TinyMCE-flickering-Firefox.patch.6 /tmp/
RUN set -e -x;                                                               \
    apt -qy install patch;                                                   \
    for wp in /wp/*; do                                                      \
        cd $wp ;                                                             \
        major=$(echo ${wp#"/wp/"} |cut -d. -f1);                             \
        minor=$(echo ${wp#"/wp/"}  |cut -d. -f2);                            \
        if [ $((major)) -eq 5 ] && [ $((minor)) -lt 6 ]; then                \
          patch -p0 -F3 < /tmp/wordpress-anywhere.patch.5.5;                 \
        else                                                                 \
          patch -p0 -F3 < /tmp/wordpress-anywhere.patch.5.8;                 \
        fi;                                                                  \
        if [ $((major)) -eq 6 ]; then                                        \
          patch -p0 -F3 < /tmp/wordpress-TinyMCE-flickering-Firefox.patch.6; \
          cp $wp/wp-includes/js/tinymce/plugins/wordpress/plugin.js          \
            $wp/wp-includes/js/tinymce/plugins/wordpress/plugin.min.js;      \
        fi;                                                                  \
    done;                                                                    \
    apt -qy remove --purge patch;                                            \
    rm /tmp/wordpress-anywhere.patch.5.5;                                    \
    rm /tmp/wordpress-anywhere.patch.5.8;                                    \
    rm /tmp/wordpress-TinyMCE-flickering-Firefox.patch.6;

######################################################################
# Install and patch plugins and themes
######################################################################

ADD install-plugins-and-themes.py clearstatcache-wp-import.patch /tmp/
# Get all plugins and themes (in "auto" mode) out of the Ansible
# `plugins.yml` file:
ARG INSTALL_AUTO_FLAGS
RUN set -e -x; for wp in /wp/*; do cd $wp ;                                                      \
        wpversion=$(echo ${wp#"/wp/"});                                                          \
        /tmp/install-plugins-and-themes.py auto ${INSTALL_AUTO_FLAGS} --wp-version ${wpversion}; \
    done

# Special treatment for tinymce-advanced, whose version scheme follows
# WordPress' starting at 5.2... and ending at 5.6
RUN set -e -x; for wp in /wp/*; do                                         \
  cd $wp;                                                                  \
  wpmajorminor="$(basename $wp | cut -d. -f1-2)";                          \
  curl -q https://api.wordpress.org/plugins/info/1.0/tinymce-advanced.json \
  | jq -r '.versions | to_entries as $versions | $versions                 \
         | map(select (.key | startswith("'$wpmajorminor'"))) as $matches  \
         | if ($matches | length) == 0 then                                \
                $versions | map(select(.key | match("^[0-9.]+$")))         \
           else $matches end                                               \
         | map(.value) | last '                                            \
     | xargs -t -i curl -o tinymce-advanced.zip {} ;                       \
  rm -rf wp-content/plugins/tinymce-advanced;                              \
  (cd wp-content/plugins; unzip ../../tinymce-advanced.zip);               \
  rm tinymce-advanced.zip;                                                 \
  done

# build wp-gutenberg-epfl
RUN set -e -x; for wp in /wp/*; do                                         \
  cd $wp;                                                                  \
  (cd wp-content/plugins/wp-gutenberg-epfl;                                \
      rm -rf build; npm i --no-fund; npm run build; rm -rf node_modules);  \
  done

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
# Home built Elements
######################################################################
ARG ELEMENTS_GIT_REPOSITORY=""
ARG ELEMENTS_GIT_REF="dev"
RUN set -e -x;   env; \
    if [ -z "$ELEMENTS_GIT_REPOSITORY" ]; then exit 0; fi; \
    rm -rf /wp/*/wp-content/themes/wp-theme-2018/assets; \
    git clone "$ELEMENTS_GIT_REPOSITORY" -b "$ELEMENTS_GIT_REF" /tmp/elements_build; \
    cd /tmp/elements_build; \
    npm install --global yarn; \
    yarn; yarn build; \
    for wp in /wp/*; do cp -a dist/ $wp/wp-content/themes/wp-theme-2018/assets; done ; \
    cd; rm -rf /tmp/elements_build

######################################################################
# Symlinks in /wp
######################################################################
# We do that last for simplicity, at a small cost in build time
COPY symlink-wp-versions.sh /tmp
RUN sh /tmp/symlink-wp-versions.sh && rm /tmp/symlink-wp-versions.sh
