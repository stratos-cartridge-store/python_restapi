import web
import re
import base64
from xml.dom import minidom
import logging
import logging.config
#import config.py ;)
import config

#load cherryPyserver
from web.wsgiserver import CherryPyWSGIServer

#logging configs
logging.config.fileConfig('logging.conf')

# Initiate logger handler
logger = logging.getLogger('restapi')

#Private and cert keys
CherryPyWSGIServer.ssl_certificate = "/home/roshan/workspace/key/ssl-cert-snakeoil.pem"
CherryPyWSGIServer.ssl_private_key = "/home/roshan/workspace/key/ssl-cert-snakeoil.key"



#Home 
class Index:
    def GET(self):
        if web.ctx.env.get('HTTP_AUTHORIZATION') is not None:
            #read xml
            xmldoc = minidom.parse('items.xml')

            itemlist = xmldoc.getElementsByTagName('item')

            #from pprint import pprint
            #pprint (vars(your_object))
            #logger.debug(itemlist)

            #return item list
            return len(itemlist)

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
            if (username,password) in config.allowed:

                #logger.info('Successfully logged in')

                raise web.seeother('/')
            else:
                authreq = True
        if authreq:
            web.header('WWW-Authenticate','Basic realm="Auth example"')
            web.ctx.status = '401 Unauthorized'
            return




if __name__ == "__main__":
    app = web.application(config.urls, globals())
    app.run() 

