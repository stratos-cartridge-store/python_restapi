import web

#Routing
urls = (
    '/','Index',
    '/login','Login',
    '/getModuleList','GetModuleList',
    '/installPuppetModule/url/(.+)', 'InstallPuppetModule'
)

#allowed Users

#TODO use a database to store these data and ultimately we may need to implement auth support in order to authenticate 
allowed = (
    ('jon','pass1'),
    ('tom','pass2')
)

#puppet master module location

puppetMasterLocation = "/etc/puppet/modules/"