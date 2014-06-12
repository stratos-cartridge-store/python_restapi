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
3. /modules/puppet/{moduleName}/url/{url} : InstallPuppetModule
4. /modules/puppet/{moduleName}/progress : GetModuleInstallationProgress
5. /modules/puppet/{moduleName}/status : GetModuleStatus
6. /modules/puppet/status : GetAllModulesStatus
