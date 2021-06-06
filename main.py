#!/usr/bin/env python3

import os
import re
import time
import json
import requests
from bs4 import BeautifulSoup as bs
from influxdb import InfluxDBClient

MEASURE_RE = r'\W*\d*\.\d*'
TRUST_SSL = True

"""
Influx DB Account
Set environment variables for "INFLUX_USER" and "INFLUX_PASS",
but if you do not want to set them add your account information
in the variables below.
"""
DB_USERNAME = ''
DB_PASSWORD = ''
DB_SERVER_NAME = ''
DB_INFLUX_NAME = ''

"""
If environment variables exist use those
if not use the above variable settings.
"""
DB_USER = os.getenv("INFLUX_USER") if os.getenv("INFLUX_USER") else DB_USERNAME
DB_PASS = os.getenv("INFLUX_PASS") if os.getenv("INFLUX_PASS") else DB_PASSWORD
DB_HOST = os.getenv("INFLUX_HOST") if os.getenv("INFLUX_HOST") else DB_SERVER_NAME
DB_NAME = os.getenv("INFLUX_DB_NAME") if os.getenv("INFLUX_DB_NAME") else DB_INFLUX_NAME


def modem_url_request(url='http://192.168.100.1'):
    """
    Makes http request to Arris modem
    web page. Returns page content
    """
    try:
        r = requests.get(url).content
    except:
        r = 'failed'

    if r == 'failed':
        return 'failed'
    else:
        return r


def parse_html(content):
    soup = bs(content, 'html.parser')
    return soup


def modem_status_table(table):
    status_table = table.find_all('table', class_='simpleTable')
    return status_table


def modem_ds_table_rows(data):
    ds = data[1]
    ds = ds.find_all('tr')[2:]
    return ds


def modem_us_table_rows(data):
    us = data[-1].find_all('tr')[2:]
    return us


def strip_table_row_tags(data):
    channel_data = []
    for i in data:
        row = [td for td in i.stripped_strings]
        channel_data.append(row)
    return channel_data


def prep_influx_json(ds, us):
    modem_data = []
    DATA_TIME = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
    # Downstream Data
    for row in ds:
        channel = row[0]
        power = re.match(MEASURE_RE, row[5]).group(0)
        snr = re.match(MEASURE_RE, row[6]).group(0)
        ds_data_power = {
            'measurement': 'modem_rf_stats',
            'tags': {'direction': 'downstream', 'channel': channel, 'measure': 'power'},
            'time': DATA_TIME,
            'fields': {'power': power}
        }
        ds_data_snr = {
            'measurement': 'modem_rf_stats',
            'tags': {'direction': 'downstream', 'channel': channel, 'measure': 'snr'},
            'time': DATA_TIME,
            'fields': {'snr': snr}
        }
        modem_data.append(ds_data_power)
        modem_data.append(ds_data_snr)
    # Upstream Data
    for row in us:
        channel = row[0]
        power = re.match(MEASURE_RE, row[-1]).group(0)
        us_data = {
            'measurement': 'modem_rf_stats',
            'tags': {'direction': 'upstream', 'channel': channel, 'measure': 'power'},
            'time': DATA_TIME,
            'fields': {'power': power}
        }
        modem_data.append(us_data)
    json_body = json.dumps(modem_data)
    return json_body


def write_influxdb_data(data):
    client = InfluxDBClient(
        host=DB_HOST,
        port=8086,
        username=DB_USER,
        password=DB_PASS,
        ssl=True,
        verify_ssl=TRUST_SSL
    )
    db_write = client.write_points(
        data,
        time_precision=None,
        database=DB_NAME,
        protocol='json'
        )
    if db_write == True:
        return True
    else:
        return "Error"


def main():
    """
    main program
    """
    req = modem_url_request()
    if req == 'failed':
        pass
    else:
        html = parse_html(req)
        data_tables = modem_status_table(html)
        ds_rows = modem_ds_table_rows(data_tables)
        us_rows = modem_us_table_rows(data_tables)
        ds_rows_clean = strip_table_row_tags(ds_rows)
        us_rows_clean = strip_table_row_tags(us_rows)
        json_body = prep_influx_json(ds_rows_clean, us_rows_clean)
        json_body = json.loads(json_body)
        write_influxdb_data(json_body)


if __name__ == '__main__':
    while True:
        main()
        time.sleep(300)
