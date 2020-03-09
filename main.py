#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Common Python library imports
import os
import sys
import re
import multiprocessing as mp
import multiprocessing.queues as mpq
from lxml import html
from threading import Thread
import traceback

# Pip package imports
import pandas as pd
import requests
from requests.exceptions import Timeout, HTTPError
from loguru import logger

# Internal package imports
from config import SCRAP_CONFIG

BASE_URL = "https://www.willhaben.at/iad/immobilien/haus-mieten/haus-angebote?areaId=6&page={page}&rows=100&view="
RESULT_CSV = "output.csv"


safe_result_list = []

class WorkerQueue(mpq.Queue):
    def __init__(self, worker_fnc, *args, **kwargs):
        size = kwargs.get('size', 120)
        self.num_workers = kwargs.get('max_workers', 1)
        self.workers = []
        self.worker_fnc = worker_fnc

        # Queue.__init__(self, size)
        ctx = mp.get_context()
        super(WorkerQueue, self).__init__(size, ctx=ctx)
        self._hire_workers()

    def _hire_workers(self):
        logger.info("Queue handler is hiring \'%s\' worker." % (self.num_workers))
        for i in range(self.num_workers):
            t = Thread(target=self._worker, args=(i,))
            self.workers.append(t)
            t.daemon = True
            t.start()

    def fire_workers(self):
        logger.info("Queue handler is firing \'%s\' worker." % (self.num_workers))
        for i in range(self.num_workers):
            self.put(None)
        for t in self.workers:
            t.join()
        self.workers = []

    def _worker(self, thread_num):
        try:
            while True:
                d = self.get()
                if d is None:
                    break
                self.worker_fnc.__call__(d)
                # Do magic
        except Exception as err:
            tb = traceback.format_exc()
            logger.error("Broken Query: %s" % d)
            logger.error(tb)
        else:
            logger.info("Queue handler: \'%s\' exited safely." % (thread_num))
            return None

def get_url(url):
    logger.debug("Opening URL: \'%s\'." % url)
    try:
        response = requests.get(url, timeout=(3, 6))
        response.raise_for_status()
    except HTTPError as err:
        logger.error(err)
        return None
    return response.content

def get_last_data_id():
    try:
        df = pd.read_csv(RESULT_CSV)
        # Sort by descending dates
        df = df.sort_values(['date'], ascending=[False])
        # Return with the newest id
        return df.first()['id']
    except Exception:
        return None


def generate_list(start_page=1):
    while True:
        resp = get_url(BASE_URL.format(page=start_page))
        if resp is None:
            return
        tree = html.fromstring(resp)
        ad_element_list = tree.xpath('//div[@id="resultlist"]/article')
        for ad_element in ad_element_list:
            header_link = ad_element.xpath('.//section[@class="content-section"]/div[@class="header"]/a')
            yield header_link.attrib('href'), header_link.attrib('link')
        # increment page
        start_page += 1

def main_worker(data):
    href = data.get('href')
    ad_id = data.get('ad_id')
    if not (href or ad_id):
        logger.error('Parameters are missing')
        return

    data_dict = {
        'id': ad_id,
        'url': href,
    }
    resp = get_url(href)
    if resp is None:
        return

    tree = html.fromstring(resp)
    # Get data from config
    is_valid = True
    for data in SCRAP_CONFIG.get('datas'):
        criteria = tree.xpath(data.get('xpath'))
        if not criteria and data.get('ignoreIfEmpty'):
            continue
        val = criteria.attr(data.get('attr'))
        if not val:
            continue
        # Perform conversion
        if hasattr(data['converter'], '__call__'):
            val = data['converter'].__call__(val)
        else:
            val = data['converter']
            if not val:
                continue
        if 'validValues' in data:
            if not (val >= data['validValues']['min'] and val <= data['validValues']['max']):
                is_valid = False
                break
        elif 'validator' in data:
            if hasattr(data['validator'], '__call__'):
                if not data['validator'].__call__(val):
                    is_valid = False
                    break
            else:
                is_valid = data['validator']
        else:
            # always valid
            pass
        # Store the data if requested
        if data['store']:
            data_dict[data['name']] = val
    # If all criteria is valid store the result in DF
    if is_valid:
        safe_result_list.append(data_dict)


def main_process():
    safe_result_list = []
    q = WorkerQueue(main_worker)
    last_id = get_last_data_id()
    # Loop until HTTP error, or last id is equal with current id
    for href, ad_id in generate_list():
        print("Href: ", href)
        print("ad_id: ", ad_id)
        if ad_id == last_id:
            # Last ID reached
            break
        #q.put({'href': href, 'id': ad_id})

    # Wait for the worker threads to finish
    q.fire_workers()
    df = pd.concat(safe_result_list, ignore_index=True)
    df = df.set_index('id', drop=True)
    df.to_csv(RESULT_CSV)

if __name__ == '__main__':
    main_process()