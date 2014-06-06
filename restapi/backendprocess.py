import web
import re
import base64
from xml.dom import minidom
import logging
import logging.config
import os
import json
import sys
import subprocess
import urllib2

#dump printing
import pprint

#import config.py ;)
import conf.config

#load cherryPyserver
from web.wsgiserver import CherryPyWSGIServer

#logging configs
logging.config.fileConfig('conf/logging.conf')

# Initiate logger handler
logger = logging.getLogger('restapi')

#initiate file download logger
fileDownLoadLogger = logging.getLogger('filedownloader')

#logger.debug('module downloadable URL'+ url)

fileDownLoadLogger.debug("Download URL is = "+ sys.argv[1])

url = sys.argv[1]

hdr = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
       'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
       'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
       'Accept-Encoding': 'none',
       'Accept-Language': 'en-US,en;q=0.8',
       'Connection': 'keep-alive'}

file_name = url.split('/')[-1]

req = urllib2.Request(url, headers=hdr)

try:

    u = urllib2.urlopen(req)

    fileDownLoadLogger.debug(file_name + "File has opened")

    f = open(file_name, 'wb')

    meta = u.info()

    file_size = int(meta.getheaders("Content-Length")[0])

    fileDownLoadLogger.debug("Downloading: %s Bytes: %s" % (file_name, file_size))

    file_size_dl = 0
    block_sz = 8192

    #counter to controll number of logs line while reading file
    counter = 0

    while True:

        buffer = u.read(block_sz)

        if not buffer:
            break

        file_size_dl += len(buffer)

        f.write(buffer)

        if counter % 1000  == 0:
            status = r"%10d  [%3.2f%%]" % (file_size_dl, file_size_dl * 100. / file_size)
            status = status + chr(8)*(len(status)+1)
            fileDownLoadLogger.debug(status)
        
    	counter += 1
    f.close()
    
    fileDownLoadLogger.info(file_name + "File download finished")

    #web.header('Content-Type', 'application/json')

    #return json.dumps(url)

except urllib2.HTTPError, e:

    fileDownLoadLogger.debug("Fail to download file")

