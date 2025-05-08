import time
import argparse

from wordpresses import WordpressSite

if __name__ == '__main__':
    for wordpresssite in WordpressSite.all():
        print(wordpresssite.moniker)
        print(wordpresssite.run_cron())

    parser = argparse.ArgumentParser(description="Wordpress wp cron executor")
    
    parser.add_argument(
        '--daemon',
        action='store_true',
        help='Run the program in daemon mode (forever)'
    )
    
    args = parser.parse_args()

    if args.daemon:
        print("All done. I am going to sleep", flush=True)
        time.sleep(3600)
    else:
        exit(0)
