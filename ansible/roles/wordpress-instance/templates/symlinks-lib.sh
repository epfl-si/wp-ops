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

    retval=0
    for path in "$@"; do
        target="/wp/$path"
        [ "$(readlink $path 2>/dev/null || true)" = $target ] && continue

        retval=1
{% if ansible_check_mode %}
        echo >&2 "$path needs symlinking"
{% else %}
        rm -rf "$path"
        dir="$(dirname "$path")"
        test -d "$dir" || mkdir -p "$dir"
        ln -s "$target" "$path"
{% endif %}
    done
    return $retval
}
