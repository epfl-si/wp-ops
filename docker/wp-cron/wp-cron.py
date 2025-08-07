import time
import argparse

from wordpresses import WordpressSite
from sitemap import Sitemap

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Wordpress wp cron executor")

    parser.add_argument(
        '--daemon',
        action='store_true',
        help='Run the program in daemon mode (forever)'
    )

    parser.add_argument(
        '--pushgateway',
        type=str,
        default="pushgateway:9091",
        help='The pushgateway service host and port'
    )

    args = parser.parse_args()

    for wordpresssite in WordpressSite.all():
        wordpresssite.set_pushgateway(args.pushgateway)
        print(wordpresssite.moniker)
        print(wordpresssite.run_cron())
    
    Sitemap.create()

    if args.daemon:
        print("All done. I am going to sleep", flush=True)
        time.sleep(3600)
    else:
        exit(0)
