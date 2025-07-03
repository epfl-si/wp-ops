#!/usr/bin/env bash
#
# WordPress SBOM Generator
#
# Description:
#   This script generates a Software Bill of Materials (SBOM) in YAML format for
#   a WordPress serving image. It scans the specified wp-content directory for
#   plugins, mu-plugins, and themes, extracting their version information from
#   the main plugin file or style.css (for themes). Additionally, it attempts to
#   gather Git repository information (commit hash, branch, and repo URL) for
#   each item, if available.
#
# Usage:
#   WP_CONTENT_DIR=src/wp-content ./wp-sbom.sh
#     (default to /wp/wp-content)
#
# Output:
#   YAML-formatted SBOM listing plugins, mu-plugins, and themes with their
#   versions and Git info.
#

set -e -x

: ${WP_CONTENT_DIR:="/wp/wp-content"}

get_asset_name() {
  if [ $1 == 'mu-plugin' ]; then
    echo "$(basename $2)";
  else
    echo "$(basename $(dirname $2))";
  fi
}
get_plugin_or_theme_name() {
  cat $1 | grep -i '\(theme\|plugin\) name\s\?:' | cut -d':' -f2 | xargs
}
get_plugin_or_theme_version() {
  echo $(cat $1 | grep -i 'version\s\?:' | cut -d':' -f2)
}
get_git_hash() {
  if [ $1 == 'theme' ]; then
    git -C "$(dirname $2)" rev-parse HEAD || echo '~'
  else
    git -C "$2/.git" rev-parse HEAD || echo '~'
  fi
}
get_git_branch() {
  if [ $1 == 'theme' ]; then
    git -C "$(dirname $2)" rev-parse --abbrev-ref HEAD || echo '~'
  else
    git -C "$2/.git" rev-parse --abbrev-ref HEAD || echo '~'
  fi
}
git_repo_to_https() {
  if [ $1 == 'theme' ]; then
    (git -C "$(dirname $2)" config --get remote.origin.url || echo '~') \
    | sed -E 's#^git@([^:]+):([^/]+)/([^/]+)(\.git)?$#https://\1/\2/\3#' \
    | sed 's/\.git$//'
  else
    (git -C "$2/.git" config --get remote.origin.url || echo '~') \
    | sed -E 's#^git@([^:]+):([^/]+)/([^/]+)(\.git)?$#https://\1/\2/\3#' \
    | sed 's/\.git$//'
  fi
}

echo "_meta:"
echo "  build_on: $(date +"%Y-%m-%dT%H:%M:%S%z")"
echo
echo "wordpress_sbom:"
echo

for kind in plugin mu-plugin theme; do
  echo "  ${kind}s:"
  find ${WP_CONTENT_DIR}/${kind}s \
    -type f \
    -maxdepth 2 \
    \( -name '*.php' \) -o \
    \( -name 'style.css' -a -path '*/wp-content/themes*' \) \
    | xargs grep -l "\(Theme\|Plugin\)\sName:\s" \
    | while read filename; do \
      echo "'$(get_asset_name $kind $filename)':"
      echo -n "  name:    "; get_plugin_or_theme_name $filename
      echo -n "  version: "; get_plugin_or_theme_version $filename
      echo -n "  hash:    "; get_git_hash $kind $(dirname $filename)
      echo -n "  branch:  "; get_git_branch $kind $(dirname $filename)
      echo -n "  repo:    "; git_repo_to_https $kind $(dirname $filename)
      echo
    done | sed 's/^/    /'
done
