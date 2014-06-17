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
import pprint
import conf.config
import hashlib
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

#checksum
md5checksum = sys.argv[3]
fileDownLoadLogger.debug("Module check sum argument value is = "+ md5checksum)

#return file's md5 digest
def md5Checksum(filePath):
    with open(filePath, 'rb') as fh:
        m = hashlib.md5()
        while True:
            data = fh.read(8192)
            if not data:
                break
            m.update(data)
        return m.hexdigest()


#This function will read module name as a xml element in to progresslist.xml
def writeElemetToTheXML(moduleName,xmlFileName):
    #open a file to store inprogress module names
    import xml.etree.ElementTree as ET
    tree = ET.parse(xmlFileName)
    root = tree.getroot()
    a = ET.SubElement(root,'module')
    b = ET.SubElement(a ,'name')
    b.text=moduleName
    fileDownLoadLogger.info("writing to xml file is complete.."+moduleName)
    tree.write(xmlFileName) 

#Remove module name from progresslist.xml  file
def removeFromInProgressList(moduleName):
    import xml.etree.ElementTree as ET
    tree = ET.parse('logs/progresslist.xml')
    root = tree.getroot()
    for module in root.findall('module'):
        name = module.find('name').text
        if name==moduleName:
            root.remove(module)
            fileDownLoadLogger.info("Removed from progresslist.xml "+name) 
    tree.write('logs/progresslist.xml')

#Remove module name from progresslist.xml  file
def removeFromErrorListFile(moduleName):
    import xml.etree.ElementTree as ET
    tree = ET.parse('logs/errorlist.xml')
    root = tree.getroot()
    for module in root.findall('module'):
        name = module.find('name').text
        if name==moduleName:
            root.remove(module)
            fileDownLoadLogger.info("Removed from errorlist.xml "+name) 
    tree.write('logs/errorlist.xml')



#heders to download file
hdr = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
       'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
       'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
       'Accept-Encoding': 'none',
       'Accept-Language': 'en-US,en;q=0.8',
       'Connection': 'keep-alive'}

file_name = url.split('/')[-1]

req = urllib2.Request(url, headers=hdr)

try:

    writeElemetToTheXML(moduleName,'logs/progresslist.xml')
    removeFromErrorListFile(moduleName)

    #open request to download
    u = urllib2.urlopen(req)

    fileDownLoadLogger.debug(file_name + "File has opened")

    tmpExtractLocation = "/tmp/"+moduleName;

    fileDownLoadLogger.debug("download location" + tmpExtractLocation)    

    f = open(tmpExtractLocation+".tar.gz", 'wb')

    meta = u.info()

    file_size = int(meta.getheaders("Content-Length")[0])

    #open a log file 
    file = open("logs/modules/"+moduleName+".log", "w")

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

    #get file md5 value
    downloadedFileCheckSum = md5Checksum(tmpExtractLocation+".tar.gz")

    fileDownLoadLogger.debug("Module check sum value of downloaded file = "+ downloadedFileCheckSum)

    if downloadedFileCheckSum != md5checksum:
        fileDownLoadLogger.debug("check sum mismatched!")
        raise Exception("Downloading abort checksum mismatched..")


    logging.debug("Temp Location" + tmpExtractLocation)

    #remove folder if there is a already one
    os.system("sudo rm -rf" +" " +tmpExtractLocation)

    logging.debug("Opening Tar" + tmpExtractLocation+".tar.gz")


    tar = tarfile.open(tmpExtractLocation+".tar.gz", "r:gz")

    logging.debug("tar opened")

    
    #we create our own folder to put extract things..becasue we don't no what is the foldername of targz yet
    tar.extractall(tmpExtractLocation)

    logging.debug("tar extracted")

    # renaming directory extracted directory to module name
    from os.path import join

    for root, dirs, files in os.walk(tmpExtractLocation):
        for name in dirs:
            newname = moduleName
            os.rename(join(root,name),join(root,newname))
    #source folder
    src = tmpExtractLocation+"/"+moduleName

    logging.debug("Source folder " + src)

    #destination folder 
    dest = "/etc/puppet/modules/"

    logging.debug("Destination Folder" + dest)

    jsonSrc= "/etc/puppet/modules/"+moduleName+"/"+moduleName+".json"

    logging.debug("Json Src" + jsonSrc)

    #deployment json destination
    jsonDestination = "deploymentjsons"

    try:
        os.system("sudo mv" +" "+src+" "+dest)
        #give permission for while in order to get write permission
        os.system("sudo chmod 777 /etc/puppet/manifests/nodes.pp")
        try:
            with open("/etc/puppet/modules/"+moduleName+"/nodes.pp") as f:
                with open("/etc/puppet/manifests/nodes.pp", "a") as f1:
                    for line in f:
                        f1.write(line)
            #change puppet module to 755            
            os.system("sudo chmod 775 -R "+" "+dest+"/"+moduleName)
            #remove nodes.pp file from puppet module
            os.system("sudo rm "+" "+dest+"/"+moduleName+"/nodes.pp")
            #change the permission of manifest file
            os.system("sudo chmod 775 /etc/puppet/manifests/nodes.pp")

            #move deployment json file to the restapi/deployment json folder
            os.system("sudo mv" +" "+jsonSrc+" "+jsonDestination)

            fileDownLoadLogger.info(file_name + "File download finished")

            try:            
                removeFromInProgressList(moduleName)
                #write installed modules name to a xml file
                writeElemetToTheXML(moduleName,'logs/installedmodules.xml')

                file.write("File Download complete"+ '\n')

            except Exception as e:
                removeFromInProgressList(moduleName)
                writeElemetToTheXML(moduleName,'logs/errorlist.xml')
                fileDownLoadLogger.info('Error while removing module name from progresslist: %s' % e)
                os.system("sudo rm -rf "+" "+dest+"/"+moduleName)

        except Exception as e:
            writeElemetToTheXML(moduleName,'logs/errorlist.xml')
            removeFromInProgressList(moduleName)
            fileDownLoadLogger.info('Error while appending to the nodes.pp abort the process: %s' % e)
            os.system("sudo rm -rf "+" "+dest+"/"+moduleName)

    except OSError as e:
        writeElemetToTheXML(moduleName,'logs/errorlist.xml')
        removeFromInProgressList(moduleName)
        fileDownLoadLogger.info('Directory not copied. Error: %s' % e)
        os.system("sudo rm -rf "+" "+dest+"/"+moduleName)

except Exception as e:
    
    writeElemetToTheXML(moduleName,'logs/errorlist.xml')
    removeFromInProgressList(moduleName)
    fileDownLoadLogger.debug("Fail to download file : error is :%s" % e )
    


