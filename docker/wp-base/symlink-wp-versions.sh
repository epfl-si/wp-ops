#!/bin/sh

set -e -x

cd /wp

for version in *;   # Sorted by version since the 1970s
do
    major="$(echo "$version" |cut -d. -f1)"
    majorminor="$(echo "$version" |cut -d. -f1-2)"

    # e.g. 5 -> 5.2.4 (except for 5.3 which is not ready for prime time)
    case "$majorminor" in
        4*|5.2)
            rm -f "$major"                # best version wins, thanks to sorting order
            ln -s "$version" "$major"
            ;;
    esac

    # e.g. 5.2 -> 5.2.4 (again except for the "real" 5.3, which doesn't have a patch level yet)
    case "$version" in
        *.*.*)
            rm -f "$majorminor"
            ln -s "$version" "$majorminor"
            ;;
    esac
done
