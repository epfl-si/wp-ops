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

# As a backward compatibility measure / temporary hack, we support
# sites that symlink to /wp instead of /wp/4 or /wp/5:
for file_or_dir in 4/*; do
    ln -s $file_or_dir .
done
