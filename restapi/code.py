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

#import config.py,route.py ;)
import conf.config
import conf.route


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

def createJsonMessage(Code,Message):
    jsonMessage =   {
                      'Code': Code,
                      'Message': Message                      
                    }
    return jsonMessage

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


#install/download puppet module 
class InstallPuppetModule:
   
    def POST(self):

        if web.ctx.env.get('HTTP_AUTHORIZATION') is not None:
            try:
                web.header('Content-Type', 'application/json')

                logger.info('accessing /InstallModuel')

                user_data = web.input()

                logger.info(user_data)

                packageType = user_data.packagetype
                moduleName = user_data.modulename
                checkSum = user_data.checksum
                downloadUrl = user_data.downloadUrl

                logger.info("packagetype: "+ packageType)
                logger.info("downloadUrl: "+ downloadUrl)
                logger.info("moduleName: "+ moduleName)
                logger.info("checkSum: "+ checkSum)

                #we currently support only puppet
                if user_data.packagetype!="puppet":
                    web.ctx.status = '404 Not Found'
                    return json.dumps(createJsonMessage("404","Package type not found"))

                f = []
                for (dirpath, dirnames, filenames) in walk(conf.config.puppetMasterLocation):
                    f.extend(dirnames)
                    break

                moduleNameInLowerCase = moduleName.lower() 
                
                #if a module is already in progress return error
                import xml.etree.ElementTree as ET
                tree = ET.parse('logs/progresslist.xml')
                root = tree.getroot()
                for module in root.findall('module'):
                    name = module.find('name').text
                    if name==moduleNameInLowerCase:
                        web.ctx.status = '409 Conflict'
                        logger.info("module is already available in progress list!")
                        return json.dumps(createJsonMessage("409","requested module is currently installing..")) 
                        
                if moduleNameInLowerCase in f:
                    web.ctx.status = '409 Conflict'
                    logger.info("module is already available abort download")
                    return json.dumps(createJsonMessage("409","Module is already available in puppet master.."))  
                    
                else:
                    #start the subprocess sweet of python <3.
                    p = subprocess.Popen(['python', 'backendprocess.py' ,downloadUrl,moduleNameInLowerCase,checkSum])
                    web.ctx.status = '202 Accepted'
                    logger.info("we have accepted your request,moudle will be installed soon!!")
                    return json.dumps(createJsonMessage("202","we have accepted your request,moudle will be installed soon!!"))

            except Exception as e:
                logger.debug("Error is :%s" % e )
                web.ctx.status = '500 Internal Server Error'
                return json.dumps(createJsonMessage("500","Internal Server Error"))
                
        else:
            #logger.info('Prompting http basic auth!')
            raise web.seeother('/login')


class GetModuleInstallationLog:
    #parameters module name
    def GET(self):

        if web.ctx.env.get('HTTP_AUTHORIZATION') is not None:

            try:
                web.header('Content-Type', 'application/json')

                logger.info('accessing /GetModuleInstallationLog')

                packageType = web.input(packagetype="puppetsd")
                moduleName = web.input(modulename="nodejssd")

                packageType = packageType.packagetype
                moduleName = moduleName.modulename

                logger.info(packageType)
                logger.info(moduleName)

                #we are currently support only puppet packages
                if packageType!="puppet":
                    web.ctx.status = '404 Not Found'
                    return json.dumps(createJsonMessage("404","Package type not found"))

                path = "logs/modules/"+moduleName+".log"

                logger.info(path)
                if os.path.isfile(path):
                    f = open(path,'r')
                    myList = []
                    for line in f:
                        myList.append(line)
                       

                    return json.dumps(myList)
                    
                else:
                    web.ctx.status = '404 Not Found'
                    return json.dumps(createJsonMessage("404","log file is not found"))
                    
            except Exception as e:
                logger.debug("Error is :%s" % e )
                web.ctx.status = '500 Internal Server Error'
                return json.dumps(createJsonMessage("500","Internal Server Error"))

        else:
            #logger.info('Prompting http basic auth!')
            raise web.seeother('/login')



class GetModuleStatus:
    #parameter module name
    def GET(self):
        if web.ctx.env.get('HTTP_AUTHORIZATION') is not None:

            try:
                web.header('Content-Type', 'application/json')

                logger.info('accessing /GetModuleStatus')

                webInputObj = web.input()
            
                packageType = webInputObj.packagetype
                name = webInputObj.modulename

                logger.info("package type  "+packageType)
                logger.info("module name "+ name)

                #we are currently support only puppet packages
                if packageType!="puppet":
                    web.ctx.status = '404 Not Found'
                    return json.dumps(createJsonMessage("404","Package type not found"))


                import xml.etree.ElementTree as ET
                tree = ET.parse('logs/errorlist.xml')
                root = tree.getroot()
                for module in root.findall('module'):
                    moduleName = module.find('name').text
                    if name==moduleName:
                        return json.dumps(createJsonMessage("10","Module is in error list"))


                #logger.info(os.listdir("/home/roshan/"))
                from os import walk
                f = []
                for (dirpath, dirnames, filenames) in walk(conf.config.puppetMasterLocation):
                    f.extend(dirnames)
                    break

                if name in f:
                    return json.dumps(createJsonMessage("11","Module is installed"))
                          
                import xml.etree.ElementTree as ET
                tree = ET.parse('logs/progresslist.xml')
                root = tree.getroot()
                for module in root.findall('module'):
                    moduleName = module.find('name').text
                    if name==moduleName:
                        return json.dumps(createJsonMessage("12","Module installation is in progress"))


                #return 404 moduel not found at last
                web.ctx.status = '404 Not Found'
                return json.dumps(createJsonMessage("404","Module is not found"))
                
            except Exception as e:
                logger.debug("Error is :%s" % e )
                web.ctx.status = '500 Internal Server Error'
                return json.dumps(createJsonMessage("500","Internal Server Error"))
        else:
            #logger.info('Prompting http basic auth!')
            raise web.seeother('/login')


class GetAllModulesList:
    #parameter module name
    def GET(self):
        if web.ctx.env.get('HTTP_AUTHORIZATION') is not None:

            #python dictionary should return with list of installed modules and on progress modules
            try:

                web.header('Content-Type', 'application/json')

                logger.info('accessing /GetModuleStatus')

                webInputObj = web.input()
            
                packageType = webInputObj.packagetype
                

                logger.info("package type  "+packageType)

                #we are currently support only puppet packages
                if packageType!="puppet":
                    web.ctx.status = '404 Not Found'
                    return json.dumps(createJsonMessage("404","Package type not found"))

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

                return json.dumps(rec)

            except Exception as e:
                logger.debug("Error is :%s" % e )
                web.ctx.status = '500 Internal Server Error'
                return json.dumps(createJsonMessage("500","Internal Server Error"))

        else:
             #logger.info('Prompting http basic auth!')
             raise web.seeother('/login')

class  GetDeploymentJson:
    def GET(self):
        if web.ctx.env.get('HTTP_AUTHORIZATION') is not None:
            try:
                web.header('Content-Type', 'application/json')

                logger.info('accessing /GetModuleStatus')

                webInputObj = web.input()
            
                packageType = webInputObj.packagetype
                name = webInputObj.modulename

                logger.info("package type  "+packageType)
                logger.info("module name "+ name)

                #we are currently support only puppet packages
                if packageType!="puppet":
                    web.ctx.status = '404 Not Found'
                    return json.dumps(createJsonMessage("404","Package type not found"))

                logger.info("this is get deployment json")

                web.header('Content-Type', 'application/json')
                try:
                    import os.path
                    if not os.path.isfile("deploymentjsons/"+name+".json"):
                        web.ctx.status = '404 Not Found'
                        return json.dumps(createJsonMessage("404","Json file is not found"))

                    with open("deploymentjsons/"+name+".json") as data_file:    
                        data = json.load(data_file)
                        logger.info(data)
                    
                    return json.dumps(data)

                except Exception as e:                    
                    logger.debug("error while reading deployment json :%s" % e )
                    web.ctx.status = '500 Internal Server Error'
                    return json.dumps(createJsonMessage("500","Internal Server Error"))

            except:
                logger.debug("Error is :%s" % e )
                web.ctx.status = '500 Internal Server Error'
                return json.dumps(createJsonMessage("500","Internal Server Error"))

        else:
            #logger.info('Prompting http basic auth!')
            raise web.seeother('/login')


if __name__ == "__main__":
    app = web.application(conf.route.urls, globals())
    app.run() 

