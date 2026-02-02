#!/usr/bin/env python3

#####
# Generate prometheus metrics about the lateness how a Logstash sincedb file

import os
import time
import logging
from pathlib import Path
from datetime import datetime
from prometheus_client import start_http_server, Gauge


SINCE_DB_PATH = os.getenv("SINCE_DB_PATH")
LOG_ROOT = os.getenv("LOG_ROOT", "/wp-audit")
PORT = int(os.getenv("EXPORTER_PORT", "9105"))
INTERVAL = int(os.getenv("SCRAPE_INTERVAL", "30"))

lag_gauge = Gauge(
    "logstash_files_modification_time_delta_with_sincedb_seconds",
    "Modified time difference between the latest audit log file and sincedb file in seconds",
)


def parse_sincedb_last_modified(path):
    path = Path(path)
    mtime = path.stat().st_mtime
    return mtime


def get_last_modified_timestamp_files_from_dir(dir_path):
    latest_modified_timestamp_from_files = max(
        f.stat().st_mtime
        for f in Path(dir_path).iterdir()
        if f.is_file()
    )
    if latest_modified_timestamp_from_files:
        return latest_modified_timestamp_from_files
    return None


def collect():
    """Collect metrics from sincedb file."""
    latest_modified_file_timestamp = get_last_modified_timestamp_files_from_dir(LOG_ROOT)
    sincedb_last_modified_timestamp = parse_sincedb_last_modified(SINCE_DB_PATH)

    if sincedb_last_modified_timestamp and latest_modified_file_timestamp:
        lag_gauge.set(sincedb_last_modified_timestamp - latest_modified_file_timestamp)
    else:
        lag_gauge.set(float('nan'))


if __name__ == "__main__":
    # Validate configuration
    if not SINCE_DB_PATH:
        raise ValueError("SINCE_DB_PATH environment variable must be set")

    if not os.path.exists(SINCE_DB_PATH):
        raise FileNotFoundError(f"sincedb file not found: {SINCE_DB_PATH}")

    logging.info(f"Starting Logstash sincedb exporter on port {PORT}")
    logging.info(f"Monitoring sincedb: {SINCE_DB_PATH}")
    logging.info(f"Log root: {LOG_ROOT}")
    logging.info(f"Scrape interval: {INTERVAL}s")

    start_http_server(PORT)

    while True:
        collect()
        time.sleep(INTERVAL)
