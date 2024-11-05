FROM wordpress:6.6.2-fpm

RUN set -e -x; mkdir /wp; mv /usr/src/wordpress /wp/6.6.2

RUN set -e -x; \
    apt -qy update ; \
    apt -qy install awscli jq \
            python3 python3-pip python3-six python3-requests \
            python3-yaml git unzip nodejs npm ; \
    apt clean
  

######################################################################
# Install wp-cli
######################################################################

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
# Install and patch plugins and themes
######################################################################
# TODO: we don't want to enumerate plugins from Ansible sources anymore!
# But hey - It works.

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
# TODO: do we still need TinyMCE in a Gutenberg world?
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
