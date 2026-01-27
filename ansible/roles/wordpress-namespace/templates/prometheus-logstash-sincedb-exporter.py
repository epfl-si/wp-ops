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

offset_gauge = Gauge(
    "logstash_file_input_offset_bytes",
    "Last read offset from sincedb",
    ["path"]
)

lag_gauge = Gauge(
    "logstash_file_input_lag_seconds",
    "Seconds since file was last read",
    ["path"]
)

def parse_sincedb(path):
    entries = []

    # fetch and load all sincedb lines
    with open(path, "r") as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) < 4:
                continue

            inode, major, minor, offset = parts[:4]
            last_active = float(parts[4]) if len(parts) >= 5 else None
            file_path = parts[5] if len(parts) >= 6 else None

            entries.append({
                "inode": inode,
                "offset": int(offset),
                "last_active": last_active,
                "path": file_path
            })

    return entries

def get_last_modified_timestamp_files_from_dir(dir_path):
    latest_modified_timestamp_from_files = max(
        f.stat().st_mtime
        for f in Path(dir_path).iterdir()
        if f.is_file()
    )
    if latest_modified_timestamp_from_files:
        return datetime.fromtimestamp(latest_modified_timestamp_from_files)
    return None


def collect():
    """Collect metrics from sincedb file."""
    # last touched file from WP
    latest_modified_file_timestamp = get_last_modified_timestamp_files_from_dir(LOG_ROOT)
    now = time.time()
    sincedb_entries = parse_sincedb(SINCE_DB_PATH)

    for e in sincedb_entries:
        path = e["path"]

        offset_gauge.labels(path=path).set(e["offset"])

        if e["last_active"]:
            lag = now - e["last_active"]
            lag_gauge.labels(path=path).set(lag)

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
