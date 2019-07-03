# A library of reusable shell functions for symlinks

# Create one symlink per function argument , pointing to /wp.
#
# This template is meant to be re-used between the "create site" and
# "turn unsymlinked site to symlinked" use cases.
#
# Honor `--check` flag on the ansible-playbook command line. If any
# work was done (or would be done absent `--check`), return 1, else
# return 0.
make_symlinks_to_wp() {
    local retval

    cd "{{ wp_dir }}"

    ensure_symlink_makes_changes=0
    for path in "$@"; do
        target="$(to_dotdots "$path")wp/$path"
        ensure_symlink "$path" "$target"
    done

    ensure_symlink "wp" "/wp/4"

    return $ensure_symlink_makes_changes
}

ensure_symlink () {
  [ "$(readlink "$1" 2>/dev/null || true)" = "$2" ] && return 0
  ensure_symlink_makes_changes=1

{% if ansible_check_mode %}
          echo >&2 "$1 needs symlinking"
{% else %}
          rm -rf "$1"

          local dir
          dir="$(dirname "$1")"
          test -d "$dir" || mkdir -p "$dir"

          ln -s "$2" "$1"
{% endif %}
}

ensure_file_contains () {
    local oldfilename newfilename
    oldfilename="$1"
    newfilename="$1.NEW.$$"
    cat > "$newfilename"
    if diff "$oldfilename" "$newfilename" >&2; then
        rm "$newfilename"
        return 0
    else
{% if ansible_check_mode %}
      # We have enough chatter from "diff", above
      rm "$newfilename"
{% else %}
      mv "$newfilename" "$oldfilename"
{% endif %}
      return 1
    fi
}

# Converts a relative path to as many dotdots ("..") as it takes to
# make a symlink that brings back to the top-level directory (that is,
# one less than the number of path elements in $1)
to_dotdots() {
    local dotdots
    dotdots=$(echo "$1" | sed -e 's,/$,,g' -e 's,[^/][^/]*,..,g' |xargs dirname)

    case "$dotdots" in
        ".")     echo "";;
        *)       echo "$dotdots"/;;
    esac
}
