#!/usr/bin/evn python3
# -*- coding: utf-8 -*-

import psycopg2
import sqlite3
from web_utils import getFileMd5


db1=sqlite3.connect('sitecom.sqlite3')
cur=db1.cursor()
cur.execute("SELECT brand, model, fw_date, fw_ver, fw_desc,\
            file_name, file_sha1, file_size, \
            page_url, file_url FROM TFiles")
rows=cur.fetchall()
db1.close()
db2=psycopg2.connect(database='firmware', user='firmadyne', password='firmadyne', host='127.0.0.1')
cur = db2.cursor()
for row in rows:
    brand, model, rel_date, fw_ver, fw_desc, \
        file_name, file_sha1, file_size, \
        page_url, fw_url = row
    fw_md5 = getFileMd5(file_name)
    cur.execute("INSERT INTO image (filename,description,hash,\
                brand,model,version,file_url,rel_date,page_url,\
                file_sha1, file_size)VALUES(%s,         %s,  %s,\
                %s,   %s,     %s,      %s,      %s,      %s,\
                %s,        %s)",
                (file_name,fw_desc,fw_md5,
                 brand,model,fw_ver, fw_url, rel_date, page_url,
                 file_sha1, file_size))
db2.commit()

