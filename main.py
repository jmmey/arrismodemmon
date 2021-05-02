#!/usr/bin/env python3

import time
import requests
from bs4 import BeautifulSoup as bs

MEASURE_RE = r'\W*\d*\.\d*'
DATA_TIME = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())

def modem_url_request(url='http://192.168.100.1'):
    """
    Makes http request to Arris modem
    web page. Returns page content
    """ 
    r = requests.get(url).content
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


def main():
    url = modem_url_request()


if __name__ == '__main__':
    req = modem_url_request()
    html = parse_html(req)
    data_tables = modem_status_table(html)
    ds_rows = modem_ds_table_rows(data_tables) 
    us_rows = modem_us_table_rows(data_tables)
    ds_rows_clean = strip_table_row_tags(ds_rows)
    us_rows_clean = strip_table_row_tags(us_rows)
