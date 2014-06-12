python_restapi
==============

This API will communicate with puppet master 

Clone it first!

go to inside restapi folder

execute python code.py


REST calls
============================

1. /login : Login
2. /modules/puppet : GetModuleList'
3. /modules/puppet/(.+)/url/(.+) : InstallPuppetModule
4. /modules/puppet/(.+)/progress : GetModuleInstallationProgress
5. /modules/puppet/(.+)/status : GetModuleStatus
6. /modules/puppet/status : GetAllModulesStatus
