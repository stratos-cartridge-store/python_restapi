import web
import re
import base64
from xml.dom import minidom
import logging
import logging.config
import os
import json
import sys
import urllib2
import subprocess
from os import walk



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

#Private and cert keys
CherryPyWSGIServer.ssl_certificate = conf.config.ssl_certificate
CherryPyWSGIServer.ssl_private_key = conf.config.ssl_privatekey

#Home 
class Index:
    def GET(self):
        if web.ctx.env.get('HTTP_AUTHORIZATION') is not None:
                  
            logger.info('You are accessing /')
            #return
            return "Logged in!"

        else:
            #logger.info('Prompting http basic auth!')
            raise web.seeother('/login')

#User log in simple http basic auth via SSL
class Login:
    def GET(self):

        auth = web.ctx.env.get('HTTP_AUTHORIZATION')
        authreq = False
        if auth is None:
            authreq = True
        else:
            auth = re.sub('^Basic ','',auth)
            username,password = base64.decodestring(auth).split(':')
            if (username,password) in conf.config.allowed:

                logger.info('User Granted..')

                raise web.seeother('/')
            else:
                authreq = True
        if authreq:
            web.header('WWW-Authenticate','Basic realm="Auth example"')
            web.ctx.status = '401 Unauthorized'
            return

#Read puppet master folders and return a xml
class GetModuleList:
    def GET(self):
        if web.ctx.env.get('HTTP_AUTHORIZATION') is not None:
                  
            logger.info('accessing /getModuleList')

            #logger.info(os.listdir("/home/roshan/"))
            from os import walk

            f = []
            for (dirpath, dirnames, filenames) in walk(conf.config.puppetMasterLocation):
                f.extend(dirnames)
                break

            logger.debug(f)                
            
            
            web.header('Content-Type', 'application/json')
            return json.dumps(f)
            
            #return [name for name in os.listdir(dir)
            #if os.path.isdir(os.path.join(dir, name))]

        else:
            #logger.info('Prompting http basic auth!')
            raise web.seeother('/login')


#install/download puppet module 
class InstallPuppetModule:
   
    def POST(self,name,url,checksum):

        if web.ctx.env.get('HTTP_AUTHORIZATION') is not None:

            f = []
            for (dirpath, dirnames, filenames) in walk(conf.config.puppetMasterLocation):
                f.extend(dirnames)
                break

            moduleNameInLowerCase = name.lower() 
            
            web.header('Content-Type', 'application/json')

            #if a module is already in progress return error
            import xml.etree.ElementTree as ET
            tree = ET.parse('logs/progresslist.xml')
            root = tree.getroot()
            for module in root.findall('module'):
                name = module.find('name').text
                if name==moduleNameInLowerCase:
                    logger.info("module is already available in progress list!")  
                    return json.dumps("Module is already available in progress list!")    

            if moduleNameInLowerCase in f:
                logger.info("module is already available abort download")  
                return json.dumps("Module is already available in puppet master")
            else:
                #start the subprocess sweet of python <3.
                p = subprocess.Popen(['python', 'backendprocess.py' ,url,name,checksum])
                return json.dumps("your moudle will be installed soon!!")

        else:
            #logger.info('Prompting http basic auth!')
            raise web.seeother('/login')


class GetModuleInstallationProgress:
    #parameters module name
    def GET(self,name):

        if web.ctx.env.get('HTTP_AUTHORIZATION') is not None:

            #a=open('/home/roshan/workspace/webpy/restapi/logs/filedownload.log','rb')

            f = open("logs/modules/"+name+".log",'r')
            myList = []
            for line in f:
                myList.append(line)
           

            web.header('Content-Type', 'application/json')
            return json.dumps(myList)
            #return myList
        else:
            #logger.info('Prompting http basic auth!')
            raise web.seeother('/login')



class GetModuleStatus:
    #parameter module name
    def GET(self,name):
        if web.ctx.env.get('HTTP_AUTHORIZATION') is not None:

            web.header('Content-Type', 'application/json')

            import xml.etree.ElementTree as ET
            tree = ET.parse('logs/errorlist.xml')
            root = tree.getroot()
            for module in root.findall('module'):
                moduleName = module.find('name').text
                if name==moduleName:
                    return json.dumps("error")


            import xml.etree.ElementTree as ET
            tree = ET.parse('logs/installedmodules.xml')
            root = tree.getroot()
            for module in root.findall('module'):
                moduleName = module.find('name').text
                if name==moduleName:
                    return json.dumps("installed")

            import xml.etree.ElementTree as ET
            tree = ET.parse('logs/progresslist.xml')
            root = tree.getroot()
            for module in root.findall('module'):
                moduleName = module.find('name').text
                if name==moduleName:
                    return json.dumps("inprogress")

        else:
            #logger.info('Prompting http basic auth!')
            raise web.seeother('/login')


class GetAllModulesStatus:
    #parameter module name
    def GET(self):
        if web.ctx.env.get('HTTP_AUTHORIZATION') is not None:

            #python dictionary should return with list of installed modules and on progress modules

            #installed module list
            installedModuleList = []
            for (dirpath, dirnames, filenames) in walk(conf.config.puppetMasterLocation):
                installedModuleList.extend(dirnames)
                break

            #inprogress module lists
            inProgressModuleList = []

            import xml.etree.ElementTree as ET
            tree = ET.parse('logs/progresslist.xml')
            root = tree.getroot()
            for module in root.findall('module'):
                name = module.find('name').text
                logger.info(name)
                inProgressModuleList.append(name)

           

            #error module lists
            errorModuleList = []
            import xml.etree.ElementTree as ET
            tree = ET.parse('logs/errorlist.xml')
            root = tree.getroot()
            for module in root.findall('module'):
                name = module.find('name').text
                logger.info(name)
                errorModuleList.append(name)

    
            #merge tow lists and make a python dictionary]
            rec = {
                  'installed': installedModuleList,
                  'inprogress': inProgressModuleList,
                  'error': errorModuleList
                  }

            logger.debug(rec)

            web.header('Content-Type', 'application/json')
            return json.dumps(rec)

        else:
            #logger.info('Prompting http basic auth!')
            raise web.seeother('/login')

class  GetDeploymentJson:
    def GET(self,name):
        if web.ctx.env.get('HTTP_AUTHORIZATION') is not None:

            logger.info("this is get deployment json")

            web.header('Content-Type', 'application/json')
            try:            
                with open("deploymentjsons/"+name+".json") as data_file:    
                data = json.load(data_file)
                logger.info(data)
                
                return json.dumps(data)

            except Exception as e:
                return json.dumps("error while reading deployment json")

        else:
            #logger.info('Prompting http basic auth!')
            raise web.seeother('/login')


if __name__ == "__main__":
    app = web.application(conf.config.urls, globals())
    app.run() 

