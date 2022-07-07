#!/usr/bin/env bash
# set -e -x

# Target file
TARGET=README.md

# Markers
START=start_contributors
END=end_contributors
LEAD="^<!-- ${START} .*-->$"
TAIL="^<!-- ${END} .*-->$"

# Leave blank for no backup.
# *.bak, *.back, *.backup, *.copy, *.tmp, *.previous are git ignored
BACKUP_SUFFIX=.previous

# Target URL
# TODO: get these from the current repo
USER=epfl-si
REPO=wp-ops

# When mode:something is used
get_list_mode () {
  MODE=$(sed -n "s/^<\!-- ${START}\s.*mode:\s*\(\S*\).*$/\1/p" $TARGET)
  # default MODE is "bullet"
  [ -z "$MODE" ] && MODE="bullet"
}

# Fetch the contributors list
fetch_contributors_as_a_bullet_list () {
  CONTRIBUTORS_LIST=$(curl -s https://api.github.com/repos/${USER}/${REPO}/contributors | jq -r '.[] | "  * [@\(.login)](\(.html_url))"'| grep -v dependabot); \
  echo "${CONTRIBUTORS_LIST}" > tmp_data
}

# Trombinoscope
fetch_contributors_as_images_list () {
  CONTRIBUTORS_LIST=$(curl -s https://api.github.com/repos/epfl-si/wp-ops/contributors | jq -r '.[] | "<a href=\"\(.html_url)\"><img src=\"\(.avatar_url)\" title=\"\(.login)´s profile\" width=\"50px\" /></a>&nbsp;"'| grep -v dependabot); \
  echo "${CONTRIBUTORS_LIST}" > tmp_data
}

# Bubble
fetch_contributors_as_bubble_images_list () {
  CONTRIBUTORS_LIST=$(curl -s https://api.github.com/repos/epfl-si/wp-ops/contributors | jq -r '.[] | "![@\(.login) avatar](https://images.weserv.nl/?url=\(.avatar_url)&h=84&w=84&fit=cover&mask=circle&maxage=7d)"' | grep -v dependabot); \
  echo "${CONTRIBUTORS_LIST}" > tmp_data
}

# HTML figure
fetch_contributors_as_HTML_figures () {
  echo "HELLO AGAIN"
  CONTRIBUTORS_LIST=$(curl -s https://api.github.com/repos/epfl-si/wp-ops/contributors | \
    jq -r '.[] | "<figure><img src=\"\(.avatar_url)\" alt=\"\(.login)´s profile\" width=\"250px\" /><figcaption><a href=\"\(.html_url)\">@\(.login)</a></figcaption></figure>"' | grep -v dependabot); \
  echo "${CONTRIBUTORS_LIST}" > tmp_data
}

# Insert the contributors list between the markers
update_contributors_in_file () {
  sed -i$BACKUP_SUFFIX -e "/$LEAD/,/$TAIL/{ /$LEAD/{p; r tmp_data
}; /$TAIL/p; d }" $TARGET
}

get_list_mode
case $MODE in
[bB]ullet)
  fetch_contributors_as_a_bullet_list
  ;;
[tT]rombinoscope)
  fetch_contributors_as_images_list
  ;;
[bB]ubble)
  fetch_contributors_as_bubble_images_list
  ;;
[fF]igure)
  fetch_contributors_as_HTML_figures
  ;;
*)
  fetch_contributors_as_a_bullet_list
  ;;
esac
update_contributors_in_file

# Output the resulting file
cat $TARGET
