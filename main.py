#!/usr/bin/env python3

import time
import requests
from bs4 import BeautifulSoup as bs


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


def main():
    url = modem_url_request()


if __name__ == '__main__':
    req = modem_url_request()
    html = parse_html(req)
    data_tables = modem_status_table(html)
    ds_rows = modem_ds_table_rows(data_tables) 
    us_rows = modem_us_table_rows(data_tables)
