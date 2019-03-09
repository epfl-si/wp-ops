#!/bin/sh

set -e

PLUGINSDIR=/wp/wp-content/plugins
mkdir -p "$PLUGINSDIR" || true
cd "$PLUGINSDIR"

WORKDIR=/tmp/plugins
mkdir $WORKDIR
trap "rm -rf '$WORKDIR'" EXIT

download_and_unzip () {
    local plugin="$1"; shift
    local address="$1"
    local zipfile="/tmp/plugins/$plugin.zip"
    curl -L -o "$zipfile" "$address"
    (
        set -x
        local tmptmpdir="$(mktemp -d)"
        trap "rm -rf '$tmptmpdir'" EXIT
        cd "$tmptmpdir"
        unzip "$zipfile"
        mv * "$PLUGINSDIR/$plugin"
    )
}

download_from_github () {
    local plugin="$1"; shift
    # e.g. https://github.com/epfl-idevelop/jahia2wp/tree/master/data/wp/wp-content/plugins/EPFL-settings
    local address="$1"
    local depot="$(echo "$address" | cut -d/ -f-5)"
    local projectdir=git/"$(echo "$address" | cut -d/ -f4-5)"
    local branch="$(echo "$address" | cut -d/ -f7)"
    local subdir="$(echo "$address" | cut -d/ -f8-)"
    (
        set -x
        cd $WORKDIR
        if ! [ -d "$projectdir" ]; then
            mkdir -p "$(dirname "$projectdir")" || true
            git clone "$depot" "$projectdir"
        fi
        cd "$projectdir"; git checkout "$branch"; \
           cp -a "$subdir" "$PLUGINSDIR"/$plugin
    )
}

while IFS=, read plugin address; do
    case "$address" in
        wp) address=$(curl https://api.wordpress.org/plugins/info/1.0/"$plugin".json |jq -r '.download_link') ;;
    esac

    case "$address" in
        *zip)
            download_and_unzip "$plugin" "$address" ;;
        https://github.com/*)
            download_from_github "$plugin" "$address" ;;
        *)
            echo >&2 "Weird address: “$address”"
            exit 2 ;;
    esac
done
