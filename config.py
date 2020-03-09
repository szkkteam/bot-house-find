#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Common Python library imports
import re
import datetime as dt

# Pip package imports
from loguru import logger

# Internal package imports


RE_ONLY_NUMBER = re.compile(r'(\d+)')


SCRAP_CONFIG = {
    'datas': [
        # Date of the advertisement
        {
            'xpath': '//div[@id="box-maincontent"]/span[@id="advert-info-dateTime"]',
            'name': 'date',
            'attr': 'text',
            'store': True,
            'ignoreIfEmpty': True,
            'converter': lambda x : dt.datetime.strptime(x, '%d.%m.%Y %H:%M'),
        },
        # Ground place size
        {
            'xpath': '//div[@id="box-maincontent"]/div[@class="box-body"]/span[contains(string(), "Grundfläche")]',
            'name': 'ground_place',
            'attr': 'text',
            'store': True,
            'ignoreIfEmpty': True,
            'validValues': {
                'min': 300,
                'max': 10000
            },
            'converter': lambda x : int(RE_ONLY_NUMBER.findall(x)[0]),
        },
        # House size
        {
            'xpath': '//div[@id="box-maincontent"]/div[@class="box-body"]/span[contains(string(), "Wohnfläche")]',
            'name': 'house_size',
            'attr': 'text',
            'store': True,
            'ignoreIfEmpty': True,
            'validValues': {
                'min': 50,
                'max': 140
            },
            'converter': lambda x : int(RE_ONLY_NUMBER.findall(x)[0]),
        },
        # Number of Rooms
        {
            'xpath': '//div[@id="box-maincontent"]/div[@class="box-body"]/span[contains(string(), "Zimmer")]',
            'name': 'rooms',
            'attr': 'text',
            'store': True,
            'ignoreIfEmpty': True,
            'validValues': {
                'min': 2,
                'max': 6
            },
            'converter': lambda x : int(RE_ONLY_NUMBER.findall(x)[0]),
        },
        # Overall price
        {
            'xpath': '//div[@id="box-maincontent"]/div[@class="price-box"]/div[@id="priceBox-price")]',
            'name': 'overall_price',
            'attr': 'text',
            'store': True,
            'ignoreIfEmpty': False,
            'validValues': {
                'min': 400,
                'max': 800
            },
            'converter': lambda x : int(RE_ONLY_NUMBER.findall(x)[0]),
        },
        # Deposit
        {
            'xpath': '//div[@id="box-maincontent"]/div[@class="additional-prices"]/span[contains(string(), "Kaution")]/following-sibling::span',
            'name': 'deposit',
            'attr': 'text',
            'store': True,
            'ignoreIfEmpty': True,
            'validValues': {
                'min': 0,
                'max': 2000
            },
            'converter': lambda x : int(RE_ONLY_NUMBER.findall(x)[0]),
        },
        # Provision
        {
            'xpath': '//div[@id="box-maincontent"]/div[@class="additional-prices"]/span[contains(string(), "Provision")]/following-sibling::span',
            'name': 'provision',
            'attr': 'text',
            'store': True,
            'ignoreIfEmpty': True,
            'validator': False,
            'converter': lambda x : RE_ONLY_NUMBER.findall(x)[0],
        },
        # Address
        {
            'xpath': '//div[@id="box-maincontent"]/div[@class="additional-prices"]/div[@class="right"]/dd[@itemprop="Address"]',
            'name': 'address',
            'attr': 'text',
            'store': True,
            'ignoreIfEmpty': True,
            'validator': True,
            'converter': lambda x : x.replace('<br>', ' '),
        }
    ]
}