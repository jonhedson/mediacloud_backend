#!/usr/bin/env python
#-*- coding:utf-8 -*-
u"""
Downloads Urls parses them an store them in a Mongodb Database
Created on 25/09/13
by fccoelho
license: GPL V3 or Later
"""

__docformat__ = 'restructuredtext en'

import bs4
import feedparser
import pymongo
import logging
import requests
import settings
from multiprocessing.pool import ThreadPool
from bson.errors import InvalidDocument
from pymongo.errors import DuplicateKeyError
import time
import datetime

###########################
#  Setting up Logging
###########################
logger = logging.getLogger("Downloader")
logger.setLevel(logging.DEBUG)
# create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
fh = logging.FileHandler('/tmp/mediacloud.log')
# create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# add formatter to ch
ch.setFormatter(formatter)
fh.setFormatter(formatter)
# add ch to logger
#logger.addHandler(ch)  # uncomment for console output of messages
logger.addHandler(fh)


 ## Media Cloud database setup

client = pymongo.MongoClient(settings.MONGOHOST, 27017)
MCDB = client.MCDB
FEEDS = MCDB.feeds  # Feed collection
ARTICLES = MCDB.articles  # Article Collection


class RSSDownload(object):
    def __init__(self, url):
        self.url = url

    def parse(self):
        response = feedparser.parse(self.url)
        if response.bozo:
            logger.error("fetching %s returned an exception: %s", self.url, response.bozo_exception)
            return

        self._save_articles(response.entries)
        return ((r.title, r.link) for r in response.entries)

    def _save_articles(self, entries):
        logger.info("Downloading %s articles from %s", len(entries), self.url)
        for entry in entries:
            ks = []
            for k, v in entry.iteritems():
                if isinstance(v, time.struct_time):
                    # Convert to datetime instead of removing
                    entry[k] = datetime.datetime.fromtimestamp(time.mktime(v))
                    #ks.append(k)
            #[a.pop(i) for i in ks]

            r = requests.get(entry.link)
            # print r.encoding
            try:
                encoding = r.encoding if r.encoding is not None else 'utf8'
                entry['link_content'] = r.content.decode(encoding)
                a['pypln_json'] = send_pypln(a['link_content']).json()
                #print a['pypln_json']
            except UnicodeDecodeError:
                print "could not decode page as ", encoding
                continue
            # Turn the tags field into a simple list of tags
            try:
                entry['tags'] = [i['term'] for i in entry.tags]
            except AttributeError:
                logger.info("This feed has no tags: %s", entry.link)
            try:
                entry.pop('published_parsed')
            except KeyError:
                pass
            exists = list(ARTICLES.find({"link": entry.link}))
            # print exists
            if exists == []:
                if "published" in entry:
                    # consider parsing the string datetime into a datetime object
                    pass
                try:
                    ARTICLES.insert(entry)
                except DuplicateKeyError:
                    logger.error("Duplicate article found")
                # print "inserted"

def fetch_feed(feed):
    try:
        f = RSSDownload(feed)
    except InvalidDocument:
        logger.error("This feed failed: %s", f)
    f.parse()

def send_pypln(feed_entry, url = 'http://demo.pypln.org/documents/' , data = {'corpus':'http://demo.pypln.org/corpora/15/'}, auth = ('elopes', '613722')):
    files = {'blob': feed_entry}
    resp = requests.post(url, data = data, files = files, auth=auth)
    return resp

def parallel_fetch():
    """
    Starts parallel threads to fetch feeds.
    """
    feeds = FEEDS.find()
    feedurls = []
    for f in feeds:
        t = f.get('title_detail', f.get('subtitle_detail', None))
        if t is None:
            logger.error("Feed %s does not contain ", f.get('link', None))
            continue
        try:
            feedurls.append(t["base"].decode('utf8'))
        except KeyError:
            logger.error("Feed %s does not contain base URL", f.get('link', None))
        except UnicodeEncodeError:
            logger.error("Feed %s failed Unicode decoding", f.get('link', None))
        #fetch_feed(t["base"].decode('utf8'))

    P = ThreadPool(30)
    P.map(fetch_feed, feedurls)

if __name__ == "__main__":
    parallel_fetch()
