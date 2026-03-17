import datetime
import os
import time
import argparse
import logging

from wordpresses import WordpressSite as WordpressSiteBase
from pushgateway import Pushgateway

class WordpressSite (WordpressSiteBase):
    def __init__(self, *args, **kwargs):
        super(WordpressSite, self).__init__(*args, **kwargs)

    def run_cron(self, pushgateway):
        self.status_set_key('lastCronJobRuntime',
                            datetime.datetime.now().isoformat())
        pushgateway.record_start(self)
        try:
            self.run_wp_cli(['cron', 'event', 'run', '--due-now'])
            pushgateway.record_success(self)
        except Exception:
            logging.exception("Error running wp cron")
            pushgateway.record_failure(self)

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
    pushgateway = Pushgateway(args.pushgateway)

    for wordpresssite in WordpressSite.all(
            namespace=os.getenv('K8S_NAMESPACE')):
        print(wordpresssite.moniker)
        wordpresssite.run_cron(pushgateway)
        wordpresssite.update_php_status()

    if args.daemon:
        print("All done. I am going to sleep", flush=True)
        time.sleep(3600)
    else:
        exit(0)
