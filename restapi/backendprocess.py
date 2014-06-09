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
import errno
import tarfile

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

#download url
url = urllib2.unquote(sys.argv[1])


fileDownLoadLogger.debug("Download URL is = "+ url)

#module name 
moduleName = sys.argv[2]
fileDownLoadLogger.debug("Module Name is = "+ moduleName)


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

    tmpExtractLocation = "/tmp/"+moduleName;

    fileDownLoadLogger.debug("download location" + tmpExtractLocation)    

    f = open(tmpExtractLocation+".tar.gz", 'wb')

    meta = u.info()

    file_size = int(meta.getheaders("Content-Length")[0])

    #open a log file 
    file = open("logs/modules/"+moduleName+".log", "a")

    fileDownLoadLogger.debug("Downloading: %s Bytes: %s" % (file_name, file_size))
    file.write("Downloading: %s Bytes: %s" % (file_name, file_size) + '\n')


    file_size_dl = 0
    block_sz = 8192

    #counter to controll number of logs line while reading file
    counter = 0

    

    #begins downloads
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
            file.write(status.strip() + '\n')
        
    	counter += 1

    f.close()

    #remove folder if there is a already one
    os.system("sudo rm -rf" +" " +tmpExtractLocation)

    tar = tarfile.open(tmpExtractLocation+".tar.gz", "r:gz")
    
    #we create our own folder to put extract things..becasue we don't no what is the foldername of targz yet
    tar.extractall(tmpExtractLocation)

    # renaming directory extracted directory to module name
    from os.path import join

    for root, dirs, files in os.walk(tmpExtractLocation):
        for name in dirs:
            newname = moduleName
            os.rename(join(root,name),join(root,newname))

    #source folder
    src = tmpExtractLocation+"/"+moduleName

    #destination folder 
    dest = "/etc/puppet/modules/"
    

    try:

        os.system("sudo mv" +" "+src+" "+dest)

        #give permission for while in order to get write permission
        os.system("sudo chmod 777 /etc/puppet/manifests/nodes.pp")

        try:
            with open("/etc/puppet/modules/"+moduleName+"/nodes.pp") as f:
                with open("/etc/puppet/manifests/nodes.pp", "a") as f1:
                    for line in f:
                        f1.write(line)

            os.system("sudo chmod 775 -R "+" "+dest+"/"+moduleName)
            os.system("sudo rm "+" "+dest+"/"+moduleName+"/nodes.pp")
            os.system("sudo chmod 775 /etc/puppet/manifests/nodes.pp")

            fileDownLoadLogger.info(file_name + "File download finished")
            file.write("Is file download complete??"+ '\n')
            file.write("yes")

        except Exception as e:
            fileDownLoadLogger.info('Error while appending to the nodes.pp abort the process: %s' % e)
            os.system("sudo rm -rf "+" "+dest+"/"+moduleName)

    except OSError as e:
        fileDownLoadLogger.info('Directory not copied. Error: %s' % e)

    #web.header('Content-Type', 'application/json')

    #return json.dumps(url)

except urllib2.HTTPError, e:

    fileDownLoadLogger.debug("Fail to download file")
    fileDownLoadLogger.debug("I/O error({0}): {1}".format(e.errno, e.strerror))
