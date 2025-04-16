#!/bin/bash

set -e -x

###################################################################
# Install EPFL-flavored WordPress, plugins and themes
#
# Prerequisites:
#
# - `git`, `awscli`, `unzip`, `patch` (as well as `grep`, `sed`, etc.)
# - Working `wp` CLI tool (which itself requires PHP CLI and a number of
#   PHP extensions for it, such as `php-mysql`, `php-zip` and more)
# - Polylang extensions to the `wp` CLI tool
# - A number of `.patch` and `.json` files in /tmp/
# - Current directory must be writable
# - (Optional) `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`
#      environment variables
###################################################################

targetdir="$1/$2"
version="$2"
major="$(echo "$version" | cut -d. -f1)"
minor="$(echo "$version" | cut -d. -f2)"

S3_REGION=us-east-1
S3_URL=https://s3.epfl.ch/
S3_BASEDIR=s3://svc0041-c1561ba80625465c2a53f01693922e7c

main () {
    mkdir -p "$targetdir"
    wp --allow-root --path="$targetdir" core download --version="$version"
    delete_stock_wp_content

    if [ "$major" = 6 ]; then
        patch_tinymce_flickering_firefox
    fi

    install_themes
    install_mu_plugins

    install_tinymce_advanced_plugin /tmp/tinymce-advanced-versions.json
    hotfix_tinymce_advanced_classic_paragraph

    for official_plugin in \
        flowpaper-lite-pdf-flipbook very-simple-meta-description \
        ewww-image-optimizer wordpress-importer ; do
        install_plugin_wordpress_official "$official_plugin"
    done

    ( cd "$targetdir"/wp-content/plugins/wordpress-importer ;
      git apply < /tmp/clearstatcache-wp-import.patch )

    install_plugin_zip polylang https://downloads.wordpress.org/plugin/polylang.3.6.7.zip
    # 20250401 (not an April Fool's joke...): we are not sure why there is this `did_action`
    # escape... But we did determine that short-circuiting it cures WPN-336.
    sed -i.orig 's|! did_action...pll_language_defined...|true|' "$targetdir"/wp-content/plugins/polylang/frontend/choose-lang-url.php

    install_plugin_zip redirection https://downloads.wordpress.org/plugin/redirection.5.5.2.zip

    # Some of these plugins are commercial plugins that we pay for;
    # others have been discontinued. We don't want them publicly
    # accessible, resp. we can't find them on the Internet anymore; so
    # we keep them on our S3-compatible Scality server.
    if [ -n "$AWS_ACCESS_KEY_ID" -a -n "$AWS_SECRET_ACCESS_KEY" ]; then
        # find-my-blocks: changed authors in the 3.6.x release cycle,
        # new author dropped our previous contributions
        install_plugin_s3 find-my-blocks-3.5.6.zip
        # Paid-for plugins - pretty much *the* reason why we
        # build in our private cloud.
        install_plugin_s3 wpforms.1.9.4.zip
        install_plugin_s3 wpforms-surveys-polls.1.15.0.zip
        # Additionally this last one is stuck in the past:
        install_plugin_s3 wp-media-folder.5.9.13.zip
    fi

    for homemade_or_forked_plugin in \
        wp-plugin-epfl-coming-soon wordpress.plugin.tequila \
        wp-plugin-epfl-settings \
        wp-plugin-epfl-remote-content \
        wp-plugin-epfl-content-filter \
        wp-plugin-enlighter \
        wp-plugin-epfl-intranet  \
        wp-plugin-epfl-library \
        wp-plugin-epfl-diploma-verification \
        wp-plugin-epfl-partner-universities \
        wp-plugin-epfl-404 \
        wp-gutenberg-epfl  \
        wp-plugin-epfl-courses-se \
        wp-plugin-epfl-restauration \
        wp-plugin-epfl-cache-control \
        wordpress.plugin.accred \
        wp-plugin-epfl-menus \
        ; do
        install_plugin_git "https://github.com/epfl-si/$homemade_or_forked_plugin"
    done

    install_plugin_zip wpforms-epfl-payonline https://github.com/epfl-si/wpforms-epfl-payonline/releases/latest/download/wpforms-epfl-payonline.zip

    install_language_pack "fr_FR"

    chown -R root:root "$targetdir"
    chmod -R u=rwX,g=rX,o=rX "$targetdir"
}

delete_stock_wp_content () {
    (
        cd "$targetdir"
        rm -rf wp-content/plugins/akismet \
           wp-content/plugins/hello.php   \
           wp-content/themes/twenty*      \
           */wp-activate.php              \
           wp-config-sample.php
    )
}

patch_tinymce_flickering_firefox () {
    (
        cd $targetdir
        patch -p0 -F3 < /tmp/wordpress-TinyMCE-flickering-Firefox.patch.6
        cp wp-includes/js/tinymce/plugins/wordpress/plugin{,.min}.js
    )
}

hotfix_tinymce_advanced_classic_paragraph () {
    (
        cd $targetdir
        sed -i -e 's|\(.\)=\(window.tinymce.get(`editor-${e}`);\)|\1 = \2 if (!\1) return;|g' \
            wp-content/plugins/tinymce-advanced/block-editor/classic-paragraph.js
    )
}

install_themes () {
    (
        cd $targetdir/wp-content
        rm -rf themes
        git clone https://github.com/epfl-si/wp-theme-2018 themes
    )
}

install_mu_plugins () {
    (
        cd $targetdir/wp-content
        rm -rf mu-plugins
        git clone https://github.com/epfl-si/wp-mu-plugins mu-plugins
    )
}

install_tinymce_advanced_plugin () {
    local versions_json_file="$1"
    jq -r '.versions | to_entries as $versions | $versions
          | map(select (.key | startswith("'$wpmajorminor'"))) as $matches
          | if ($matches | length) == 0 then
                 $versions | map(select(.key | match("^[0-9.]+$")))
            else $matches end
          | map(.value) | last ' < /tmp/tinymce-advanced-versions.json \
      | xargs -t -i curl -o tinymce-advanced.zip {}

    mkdir -p "$targetdir"/wp-content/plugins
    ( cd "$targetdir"/wp-content/plugins; unzip ~-/tinymce-advanced.zip )
    rm tinymce-advanced.zip
}


install_plugin_git () {
    url="$1"
    opt_branch="$2"
    (
        mkdir -p "$targetdir"/wp-content/plugins
        cd "$targetdir"/wp-content/plugins
        if [ -n "$opt_branch" ]; then
            git clone -b "$opt_branch" "$url"
        else
            git clone "$url"
        fi
        rename_plugin_dir "$(basename "$1")"
    )
}

install_plugin_zip () {
    plugin_name="$1"
    url="$2"
    (
        mkdir -p "$targetdir"/wp-content/plugins
        cd "$targetdir"/wp-content/plugins
        zip="${plugin_name}.zip"
        curl -L -o "$zip" "$url"
        unzip "$zip"

        # Some zip files are packed wrong inside:
        rename_plugin_dir "$(unzip -l "$zip" | sed -n 's|^.* \([^ ]*\)*/.*$|\1|p' | head -1)"

        rm "$zip"; rm -rf __MACOSX
    )
}

install_plugin_wordpress_official () {
    install_plugin_zip "$1" "https://downloads.wordpress.org/plugin/${1}.zip"
}

install_plugin_s3 () {
    aws --endpoint-url=$S3_URL --region=$S3_REGION s3 cp \
            "$S3_BASEDIR/$1" .
    (
        mkdir -p "$targetdir"/wp-content/plugins
        cd "$targetdir"/wp-content/plugins
        zip=~-/"$(basename "$1")"
        unzip "$zip"

        # Some zip files are packed wrong inside:
        rename_plugin_dir "$(cd /tmp; unzip -l "$(basename "$zip")" | sed -n 's|^.* \([^ ]*\)*/.*$|\1|p' | head -1)"

        rm "$zip"; rm -rf __MACOSX
    )
}

rename_plugin_dir () {
    (
        cd "$targetdir"/wp-content/plugins
        local canonical_name="$(plugin_canonical_name "$1")"
        if [ "$1" != "$canonical_name" ] ; then
            mv "$1" "$canonical_name"
        fi
    )
}

# Return the “canonical” name for a plugin directory
plugin_canonical_name () {
    local plugin_dir="$(echo "$1" | cut -d/ -f1)"
    local plugin_dir_sans_versions="$(echo "$plugin_dir" | sed 's/-[0-9].*[.].*//')"
    if [ "$plugin_dir_sans_versions" != "$plugin_dir" ]; then
        echo "$plugin_dir_sans_versions"
        return 0
    fi

    case "$plugin_dir" in
        wp-plugin-epfl-content-filter) echo "EPFL-Content-Filter" ;;
        wp-plugin-epfl-remote-content) echo "epfl-remote-content-shortcode" ;;
        wp-plugin-epfl-cache-control) echo "epfl-cache-control" ;;
        wp-plugin-epfl-library) echo "EPFL-Library-Plugins" ;;
        wp-plugin-epfl-settings) echo "EPFL-settings" ;;
        wp-plugin-*) echo "$plugin_dir" | cut -d- -f3- ;;
        wordpress.plugin.*) echo "$plugin_dir" | cut -d. -f3- ;;
        *) echo "$plugin_dir" ;;
    esac
}

# Install the specified language pack, e.g. fr_FR
install_language_pack () {
    curl -s -L -o /tmp/${1}.zip https://downloads.wordpress.org/translation/core/${version}/${1}.zip
    mkdir -p ${targetdir}/wp-content/languages/
    unzip /tmp/${1}.zip -d ${targetdir}/wp-content/languages/
}

main
