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
    def GET(self,url,name):

        #puppet module URL
        #url = "https://www.dropbox.com/meta_dl/eyJzdWJfcGF0aCI6ICIiLCAidGVzdF9saW5rIjogZmFsc2UsICJzZXJ2ZXIiOiAiZGwuZHJvcGJveHVzZXJjb250ZW50LmNvbSIsICJpdGVtX2lkIjogbnVsbCwgImlzX2RpciI6IGZhbHNlLCAidGtleSI6ICI5eWM2NXA3YjJoa3c5dDMifQ/AAM1sXjadDd1s42Ez83xcC8mQSd9U7IFrfdIRl-JqWp07g?dl=1"

        #name = "mymodule"

        #logger.info(os.listdir("/home/roshan/"))
        from os import walk

        f = []
        for (dirpath, dirnames, filenames) in walk(conf.config.puppetMasterLocation):
            f.extend(dirnames)
            break

        moduleNameInLowerCase = name.lower() 
        
        web.header('Content-Type', 'application/json')

        if moduleNameInLowerCase in f:
            logger.info("module is already available abort download")  
            return json.dumps("Module is already available in puppet master")
        else:
            #start the subprocess sweet of python <3.
            p = subprocess.Popen(['python', 'backendprocess.py' ,url,name])
            return json.dumps("your moudle will be installed soon!! see progress feature will be  available soon!!")

            

if __name__ == "__main__":
    app = web.application(conf.config.urls, globals())
    app.run() 

