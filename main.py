#!/usr/bin/env python3

import os
import re
import time
import requests
from dotenv import load_dotenv
from bs4 import BeautifulSoup as bs
from influxdb_client import InfluxDBClient, WriteOptions

# ---------------------------------
# Load in environment variables
# ---------------------------------
load_dotenv()

# Influxdb2 API URL
DB_URL = os.getenv("DB_URL")
# Influxdb2 API Token
DB_TOKEN = os.getenv("DB_TOKEN")
# Influxdb2 ORG ID
DB_ORG = os.getenv("DB_ORG")
# Influxdb2 Bucket ID
DB_BUCKET = os.getenv("DB_BUCKET")
# Modem sample rate in seconds (int)
MODEM_DATA_SAMPLE_RATE = int(os.getenv("MODEM_SAMPLE_RATE"))

# ------------------------------------------
# Regular expression to search modem data
# ------------------------------------------
MEASURE_RE = r"\W*\d*\.\d*"


def modem_url_request(url="http://192.168.100.1"):
    """
    Makes http request to Arris modem
    web page. Returns page content
    """
    try:
        r = requests.get(url).content
    except:
        r = "failed"

    if r == "failed":
        return "failed"
    else:
        return r


def parse_html(content):
    soup = bs(content, "html.parser")
    return soup


def modem_status_table(table):
    status_table = table.find_all("table", class_="simpleTable")
    return status_table


def modem_ds_table_rows(data):
    ds = data[1]
    ds = ds.find_all("tr")[2:]
    return ds


def modem_us_table_rows(data):
    us = data[-1].find_all("tr")[2:]
    return us


def strip_table_row_tags(data):
    channel_data = []
    for i in data:
        row = [td for td in i.stripped_strings]
        channel_data.append(row)
    return channel_data


def prep_influx_data(ds, us) -> dict:
    modem_data = []
    DATA_TIME = int(time.time())
    # Downstream Data
    for row in ds:
        channel = row[0]
        channel = int(channel)
        power = re.match(MEASURE_RE, row[5]).group(0)
        power = float(power)
        snr = re.match(MEASURE_RE, row[6]).group(0)
        snr = float(snr)
        ds_data_power = {
            "measurement": "modem_rf_stats",
            "tags": {"direction": "downstream", "channel": channel, "decibels": "dBmv"},
            "fields": {"downstream_power": power},
            "time": DATA_TIME,
        }
        ds_data_snr = {
            "measurement": "modem_rf_stats",
            "tags": {"direction": "downstream", "channel": channel, "decibels": "dB"},
            "fields": {"signal_to_noise": snr},
            "time": DATA_TIME,
        }
        modem_data.append(ds_data_power)
        modem_data.append(ds_data_snr)
    # Upstream Data
    for row in us:
        channel = row[0]
        channel = int(channel)
        power = re.match(MEASURE_RE, row[-1]).group(0)
        power = float(power)
        us_data = {
            "measurement": "modem_rf_stats",
            "tags": {"direction": "upstream", "channel": channel, "decibels": "dBmv"},
            "fields": {"upstream_power": power},
            "time": DATA_TIME,
        }
        modem_data.append(us_data)
    return modem_data


def influxdb2_writer(input_data):
    with InfluxDBClient(url=DB_URL, token=DB_TOKEN, org=DB_ORG) as client:
        with client.write_api(
            write_options=WriteOptions(
                batch_size=500,
                flush_interval=10_000,
                jitter_interval=2_000,
                retry_interval=5_000,
                max_retries=5,
                max_retry_delay=30_000,
                exponential_base=2,
            )
        ) as _write_client:
            try:
                _write_client.write(DB_BUCKET, DB_ORG, input_data, write_precision="s")
            except:
                pass


def main():
    """
    main program
    """
    req = modem_url_request()
    if req == "failed":
        pass
    else:
        html = parse_html(req)
        data_tables = modem_status_table(html)
        ds_rows = modem_ds_table_rows(data_tables)
        us_rows = modem_us_table_rows(data_tables)
        ds_rows_clean = strip_table_row_tags(ds_rows)
        us_rows_clean = strip_table_row_tags(us_rows)
        modem_data = prep_influx_data(ds_rows_clean, us_rows_clean)
        influxdb2_writer(modem_data)


if __name__ == "__main__":
    while True:
        main()
        time.sleep(MODEM_DATA_SAMPLE_RATE)
