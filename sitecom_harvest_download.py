#!/usr/bin/env python3
# coding: utf-8
from datetime import datetime
from os import path
import os
import sys
from pyquery import PyQuery as pq
import sqlite3
from web_utils import safeFileName, getFileSha1
from web_utils import cookie_friendly_download
from my_utils import uprint
import re
import urllib
import ipdb
import traceback

conn=None
store_dir=('./output/sitecom/')
os.makedirs(store_dir, exist_ok=True)
startTrail=[]
prevTrail=[]


def getStartIdx():
    global startTrail
    if startTrail:
        return startTrail.pop(0)
    else:
        return 0


def sql(query:str, var=None):
    global conn
    csr=conn.cursor()
    try:
        if var:
            rows = csr.execute(query,var)
        else:
            rows = csr.execute(query)
        if not query.startswith('SELECT'):
            conn.commit()
        if query.startswith('SELECT'):
            return rows.fetchall()
        else:
            return
    except sqlite3.Error as ex:
        print(ex, file=sys.stderr)
        raise ex


def parse_download_page(page_url):
    global prevTrail
    d = pq(url=page_url)
    brand='Sitecom'; revision=''; trailStr=''
    try:
        pname = d('h1.product-name')[0].text_content().strip()
    except IndexError:
        print('%s does NOT exist'%page_url)
        return
    model = d('h2.product-number')[0].text_content().strip()
    for idx, item in enumerate(d('li.download-item'), start=getStartIdx()):
        try:
            title = item.cssselect('h3.thin')[0].text_content()
        except IndexError:
            continue
        if 'firmware' not in title.lower():
            continue

        fw_date = item.cssselect('small')[0].text_content()
        # 'Publication date \r: 18 January 2016'
        fw_date = fw_date.split('\r')[1].strip(': ')
        # '18 January 2016'
        fw_date = datetime.strptime(fw_date, '%d %B %Y')

        fw_ver = item.cssselect('.download-text-title')[0].text_content()
        # 'Version number\r: 2.11'
        fw_ver = fw_ver.split('\r')[-1].strip(': ')
        # '2.11'

        fw_desc = d('.download-item div')[0].text_content().strip()
        # 'Changed:\n\n\n\tAdd timeout to check DNS alive\n\tAdd procedure to
        # verify ipv4 and ipv6 on ppp session"

        fw_url = item.cssselect('a')[0].attrib['href']
        try:
            uprint('start to download %s'% fw_url)
            local_file_path = cookie_friendly_download(page_url, fw_url, store_dir, timeout=1000)
        except urllib.error.HTTPError:
            print(ex)
            continue
        except OSError as ex:
            if ex.errno == 28:
                print(ex);print('[Errno 28] No space left on device')
                break
        except Exception as ex:
            ipdb.set_trace()
            traceback.print_exc()
            continue
        file_sha1=getFileSha1(local_file_path)
        file_size=path.getsize(local_file_path)
        uprint('file_path="%s", file_size=%s, file_sha1=%s'%(local_file_path, file_size, file_sha1))

        trailStr=str(prevTrail+[idx])
        sql("INSERT OR REPLACE INTO TFiles"
            "( brand, model, revision,"
            " fw_date, fw_ver, fw_desc, "
            " file_name, file_sha1, file_size, "
            "page_url,file_url,tree_trail) VALUES"
            "(:brand,:model,:revision,"
            ":fw_date,:fw_ver,:fw_desc,"
            ":local_file_path,:file_sha1,:file_size,"
            ":page_url,:fw_url,:trailStr)",locals())



def main():
    global conn, startTrail, prevTrail
    startTrail = [int(re.search(r'\d+', _).group(0)) for _ in sys.argv[1:]]
    conn=sqlite3.connect('sitecom.sqlite3')
    sql(
        "CREATE TABLE IF NOT EXISTS TFiles("
        "id INTEGER NOT NULL,"
        "brand TEXT,"
        "model TEXT,"
        "revision TEXT,"
        "fw_date DATE,"
        "fw_ver TEXT,"
        "fw_desc TEXT,"
        "file_name TEXT,"
        "file_size INTEGER,"
        "page_url TEXT,"
        "file_url TEXT,"
        "tree_trail TEXT,"
        "file_sha1 TEXT,"
        "PRIMARY KEY (id)"
        "UNIQUE(model,revision,file_name)"
        ");")

    d = pq(url='http://www.sitecomlearningcentre.com/')
    model_urls = sorted(list(set(_ for _ in [_.attrib['href'] for _ in d('ul#product-select a')] if _!='#')))
    startIdx = getStartIdx()
    for idx in range(startIdx, len(model_urls)):
        prevTrail+=[idx]
        parse_download_page(path.join(model_urls[idx], 'downloads'))
        prevTrail.pop()


if __name__=='__main__':
    main()


