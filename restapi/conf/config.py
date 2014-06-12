import web

#Routing
urls = (
    '/','Index',
    '/login','Login',
    '/modules/puppet','GetModuleList',
    '/modules/puppet/(.+)/url/(.+)', 'InstallPuppetModule',
    '/modules/puppet/(.+)/progress', 'GetModuleInstallationProgress',
    '/modules/puppet/(.+)/status', 'GetModuleStatus',
    '/modules/puppet/status','GetAllModulesStatus'
)

#allowed Users

#TODO use a database to store these data and ultimately we may need to implement auth support in order to authenticate 
allowed = (
    ('jon','pass1'),
    ('tom','pass2')
)

#puppet master module location

puppetMasterLocation = "/etc/puppet/modules/"

ssl_certificate = "/home/roshan/workspace/key/ssl-cert-snakeoil.pem"
ssl_privatekey = "/home/roshan/workspace/key/ssl-cert-snakeoil.key"