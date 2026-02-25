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

ADD wordpress-TinyMCE-flickering-Firefox.patch.6 /tmp/
ADD clearstatcache-wp-import.patch /tmp/

COPY install-wordpress.sh /tmp
RUN chmod +x /tmp/install-wordpress.sh

# 💡 The Docker cache unfortunately has no way of knowing that you
# `git push`ed something. Here is a way to force a rebuild everytime,
# regardless of the cached state (on your workstation) or lack thereof
# (in a cloud build).
# ADD "https://www.random.org/cgi-bin/randbyte?nbytes=10&format=h" /tmp/cachebuster

ARG WORDPRESS_VERSION="6.9"
ARG AWS_ACCESS_KEY_ID
ARG AWS_SECRET_ACCESS_KEY
RUN set -e -x; case $WORDPRESS_VERSION in                                 \
        latest) /tmp/install-wordpress.sh /wp --alpha ;;                  \
        *)      /tmp/install-wordpress.sh /wp $WORDPRESS_VERSION ;;       \
    esac

######################################################################
# Generate the Software Bill of Materials (SBOM) of the WordPress installation
######################################################################
COPY wp-sbom.sh /tmp
RUN chmod +x /tmp/wp-sbom.sh
RUN set -e -x;  \
      WP_CONTENT_DIR=/wp/wp-content /tmp/wp-sbom.sh > /wp/wp-bom.yaml

RUN rm /tmp/*.patch* /tmp/*.sh

######################################################################
# Build and install JavaScript / CSS assets
######################################################################

# build wp-gutenberg-epfl
RUN cd /wp/wp-content/plugins/wp-gutenberg-epfl;                            \
      rm -rf build; npm i --no-fund; npm run build; rm -rf node_modules

######################################################################
# Copy global error pages
######################################################################
COPY wp-error-pages /wp/wp-error-pages

FROM scratch

COPY --from=builder /wp /wp
COPY --from=builder /usr/local/bin/wp /usr/local/bin/wp
