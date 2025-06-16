FROM ubuntu:jammy AS builder

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get -qy update
RUN apt-get -qy install curl
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
RUN apt-get -qy install \
    php-cli php-curl php-gd php-ldap php-mbstring php-mysql php-xml php-zip \
    composer pipx nodejs yarn jq unzip patch git
RUN PIPX_BIN_DIR=/usr/local/bin pipx install awscli

######################################################################
# Install wp-cli
######################################################################

COPY wp-cli-config.yml /wp/wp-cli/
RUN curl -o /wp/wp-cli/wp-cli.phar https://raw.githubusercontent.com/wp-cli/builds/gh-pages/phar/wp-cli.phar

COPY wp.sh /usr/local/bin/wp

RUN mkdir /wp/wp-cli/packages; \
    wp --allow-root package install https://github.com/epfl-si/polylang-cli/archive/master.zip

######################################################################
# Install and patch WordPresses and dependencies
######################################################################

ADD http://api.wordpress.org/core/stable-check/1.0/ /tmp/wordpress-versions.json
ADD https://api.wordpress.org/plugins/info/1.0/tinymce-advanced.json /tmp/tinymce-advanced-versions.json

ADD wordpress-TinyMCE-flickering-Firefox.patch.6 /tmp/
ADD clearstatcache-wp-import.patch /tmp/

COPY install-wordpress.sh /tmp
RUN chmod +x /tmp/install-wordpress.sh

# 💡 The Docker cache unfortunately has no way of knowing that you
# `git push`ed something. Here is a way to force a rebuild everytime,
# regardless of the cached state (on your workstation) or lack thereof
# (in a cloud build).
ADD "https://www.random.org/cgi-bin/randbyte?nbytes=10&format=h" /tmp/cachebuster

ARG WORDPRESS_VERSION="6.7"
ARG AWS_ACCESS_KEY_ID
ARG AWS_SECRET_ACCESS_KEY
RUN set -e -x; cd /tmp;                                                   \
    version=$(case "$WORDPRESS_VERSION" in                                \
      latest) jq -r 'keys[]';;                                            \
      *)      jq -r 'keys[] | select(match("^'${WORDPRESS_VERSION}'"))';; \
    esac < /tmp/wordpress-versions.json | sort -n -r | head -1);          \
    /tmp/install-wordpress.sh /wp "$version"

RUN rm /tmp/*.patch* /tmp/*.sh /tmp/*.json

######################################################################
# Build and install JavaScript / CSS assets
######################################################################

# build wp-gutenberg-epfl
RUN set -e -x; for wp in /wp/*/wp-content; do                              \
  (cd $wp/plugins/wp-gutenberg-epfl;                                       \
      rm -rf build; npm i --no-fund; npm run build; rm -rf node_modules);  \
  done

# build epfl-elements
ARG ELEMENTS_GIT_REPOSITORY=""
ARG ELEMENTS_GIT_REF="dev"
RUN set -e -x;   env; \
    if [ -z "$ELEMENTS_GIT_REPOSITORY" ]; then exit 0; fi; \
    rm -rf /wp/*/wp-content/themes/wp-theme-2018/assets; \
    git clone "$ELEMENTS_GIT_REPOSITORY" -b "$ELEMENTS_GIT_REF" /tmp/elements_build; \
    cd /tmp/elements_build; \
    yarn; yarn build; \
    for wp in /wp/*/wp-content; do cp -a dist/ $wp/themes/wp-theme-2018/assets; done

######################################################################
# Symlinks in /wp
######################################################################
# We do that last for simplicity, at a small cost in build time
COPY symlink-wp-versions.sh /tmp
RUN sh /tmp/symlink-wp-versions.sh && rm /tmp/symlink-wp-versions.sh

######################################################################
# Copy global error pages
######################################################################
COPY wp-error-pages /wp/wp-error-pages

FROM scratch

COPY --from=builder /wp /wp
COPY --from=builder /usr/local/bin/wp /usr/local/bin/wp
