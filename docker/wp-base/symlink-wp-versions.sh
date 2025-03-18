#!/bin/sh

set -e -x

cd /wp

for wp_content_dir in */wp-content;   # Sorted by version since the 1970s
do
    version="$(dirname "$wp_content_dir")"
    major="$(echo "$version" |cut -d. -f1)"         # e.g. 5
    majorminor="$(echo "$version" |cut -d. -f1-2)"  # e.g. 5.2

    rm -f "$major"
    ln -s "$version" "$major"     # e.g. 5 -> 5.4  - Best version wins (i.e. runs last),
                                  # thanks to sorting order

    # e.g. 5.2 -> 5.2.4
    case "$version" in
        *.*.*)
            rm -f "$majorminor"
            ln -s "$version" "$majorminor"
            ;;
    esac
done
