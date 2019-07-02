#!/bin/bash

source ./symlinks-lib.sh

set -x

main() {
    assert_equal "$(to_dotdots "wp-admin")" ""                            "wp-admin"
    assert_equal "$(to_dotdots "wp-content/plugins/index.php")" "../../"  "wp-c/p/index.php"
    assert_equal "$(to_dotdots "wp-content/plugins/epfl")" "../../"       "wp-c/p/epfl/"
}



assert_equal() {
    if [ "$1" = "$2" ]; then
        return
    else
        echo >&2 "ASSERTION $3 FAILED: $1 = $2"
    fi
}

main
