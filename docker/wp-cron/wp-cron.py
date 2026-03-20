import datetime
import os
import time
import argparse
import logging

from wordpresses import WordpressSiteWithWpCli
from pushgateway import Pushgateway

def run_cron(wp, pushgateway):
    logging.info(f"run_cron on {wp.moniker}")
    wp.status_set_key('lastCronJobRuntime',
                        datetime.datetime.now().isoformat())
    pushgateway.record_start(wp)
    try:
        wp.run_wp_cli(['cron', 'event', 'run', '--due-now'])
        pushgateway.record_success(wp)
    except Exception:
        logging.exception("Error running wp cron")
        pushgateway.record_failure(wp)


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

    for wp in WordpressSiteWithWpCli.all(
            namespace=os.getenv('K8S_NAMESPACE')):
        run_cron(wp, pushgateway)
        wp.update_php_status()

    if args.daemon:
        print("All done. I am going to sleep", flush=True)
        time.sleep(3600)
    else:
        exit(0)
