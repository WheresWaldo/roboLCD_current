# coding=utf-8


from setuptools import setup
from setuptools.command.install import install
from setuptools.command.develop import develop
import sys

class Install_Deps(object):

    def install_deps(self):
        import subprocess
        import os
        import pip
        local_path = os.path.dirname(os.path.realpath(__file__))
        r = pip.main(['install', '--upgrade', '--no-deps', '--force-reinstall',
                      'https://github.com/Robo3D/OctoPrint-FirmwareUpdater/archive/0.2.1.zip',
                      "https://github.com/Robo3D/Meta-Reader/archive/1.1.0.zip",
                      "https://github.com/Robo3D/roboOctoprint/archive/1.4.0-rc6.zip",
                     ])
        if r is not 0:
            print("Could not install RoboLCD dependencies: Meta_Reader and/or OctoPrint_FirmwareUpdater")
            sys.exit(-1)
        else:
            pass
        #make USB stuff happen

        sh_path = local_path + '/USB_deps.sh'

        print("\n\n" + sh_path + "\n\n")
        subprocess.call(['sudo bash ' + sh_path], shell=True)




class Install_Deps(install, Install_Deps):
    def run(self):
        self.install_deps()
        install.run(self)

class Install_Deps_Dev(develop, Install_Deps):
    def run(self):
        self.install_deps()
        develop.run(self)

########################################################################################################################
### Do not forget to adjust the following variables to your own plugin.

# The plugin's identifier, has to be unique
plugin_identifier = "RoboLCD"

# The plugin's python package, should be "octoprint_<plugin identifier>", has to be unique
plugin_package = "RoboLCD"

# The plugin's human readable name. Can be overwritten within OctoPrint's internal data via __plugin_name__ in the
# plugin module
plugin_name = "RoboLCD"

# The plugin's version. Can be overwritten within OctoPrint's internal data via __plugin_version__ in the plugin module
plugin_version = "1.11.15"

# The plugin's description. Can be overwritten within OctoPrint's internal data via __plugin_description__ in the plugin
# module
plugin_description = """LCD screen for Printer"""

# The plugin's author. Can be overwritten within OctoPrint's internal data via __plugin_author__ in the plugin module
plugin_author = "Matt Pedler & Victor E Fimbres & Peri Smith"

# The plugin's author's mail address.
plugin_author_email = "Developer@robo3d.com"

# The plugin's homepage URL. Can be overwritten within OctoPrint's internal data via __plugin_url__ in the plugin module
plugin_url = "https://github.com/victorevector/RoboLCD"

# The plugin's license. Can be overwritten within OctoPrint's internal data via __plugin_license__ in the plugin module
plugin_license = "AGPLv3"

# Any additional requirements besides OctoPrint should be listed here
plugin_requires = ['qrcode>=5.3', 'sysv-ipc>=0.7.0', 'gitpython>=2.1.1']


### --------------------------------------------------------------------------------------------------------------------
### More advanced options that you usually shouldn't have to touch follow after this point
### --------------------------------------------------------------------------------------------------------------------

# Additional package data to install for this plugin. The subfolders "templates", "static" and "translations" will
# already be installed automatically if they exist.
plugin_additional_data = ['lcd', 'lcd/Icons']

# Any additional python packages you need to install with your plugin that are not contained in <plugin_package>.*
plugin_additional_packages = []

# Any python packages within <plugin_package>.* you do NOT want to install with your plugin
plugin_ignored_packages = []

# Additional parameters for the call to setuptools.setup. If your plugin wants to register additional entry points,
# define dependency links or other things like that, this is the place to go. Will be merged recursively with the
# default setup parameters as provided by octoprint_setuptools.create_plugin_setup_parameters using
# octoprint.util.dict_merge.
#
# Example:
#     plugin_requires = ["someDependency==dev"]
#     additional_setup_parameters = {"dependency_links": ["https://github.com/someUser/someRepo/archive/master.zip#egg=someDependency-dev"]}
additional_setup_parameters = {'cmdclass': {'install': Install_Deps, 'develop': Install_Deps_Dev},}

########################################################################################################################



try:
    import octoprint_setuptools
except:
    print("Could not import OctoPrint's setuptools, are you sure you are running that under "
          "the same python installation that OctoPrint is installed under?")

    sys.exit(-1)

setup_parameters = octoprint_setuptools.create_plugin_setup_parameters(
    identifier=plugin_identifier,
    package=plugin_package,
    name=plugin_name,
    version=plugin_version,
    description=plugin_description,
    author=plugin_author,
    mail=plugin_author_email,
    url=plugin_url,
    license=plugin_license,
    requires=plugin_requires,
    additional_packages=plugin_additional_packages,
    ignored_packages=plugin_ignored_packages,
    additional_data=plugin_additional_data
)

if len(additional_setup_parameters):
    from octoprint.util import dict_merge

    setup_parameters = dict_merge(setup_parameters, additional_setup_parameters)

setup(**setup_parameters)
