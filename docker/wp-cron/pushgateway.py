import time
import requests


class Pushgateway:
    def __init__(self, host_port):
        self._host_port = host_port

    def record_start(self, wp):
        self._post_pushgateway(wp, "start")

    def record_success(self, wp):
        self._post_pushgateway(wp, "success")

    def record_failure(self, wp):
        self._post_pushgateway(wp, "failure")


    def _post_pushgateway(self, wp, status):
        time_epoch = time.time()
        data = 'wp_cron_%s{wp="%s"} %d' % (status, wp.moniker, time_epoch)

        # PushGateway endpoint
        url = f"http://{self._host_port}/metrics/job/some_job"

        # Send the data using a POST request with the appropriate headers
        response = requests.post(url, data=data, headers={"Content-Type": "text/plain"})
        response.raise_for_status()
