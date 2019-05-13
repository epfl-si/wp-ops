#!/usr/bin/env python

# All rights reserved. ECOLE POLYTECHNIQUE FEDERALE DE LAUSANNE, Switzerland, VPSI, 2019
#
# Wp-veritas API fetcher, to build an ansible inventory.
# the script load the fetcher script, and send his data trough it
# the best way to use this script is to copy paste into an Inventory Scripts into AWX


import argparse
import sys

from six.moves import urllib


if __name__ == '__main__':
    # retrieve the file, always
    
    urllib.request.urlretrieve("https://gist.githubusercontent.com/jdelasoie/1ea9a69d7f5b5fbb9fb24422fe862dee/raw/", "wp_veritas_inventory.py")
    try:
        from wp_veritas_inventory import main
        main(sys.argv[1:])
    except ImportError:
        raise ImportError("Can't dynamically load wp_veritas_inventory script")
