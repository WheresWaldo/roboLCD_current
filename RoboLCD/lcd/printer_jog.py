# -*- coding: utf-8 -*-
# @Author: Matt Pedler
# @Date:   2017-05-12 10:16:15
# @Last Modified by:   Matt Pedler
# @Last Modified time: 2017-10-27 13:12:29
from .. import roboprinter
from octoprint._version import get_versions


class Printer_Jog():
    def __init__(self):
        
        self.octoprint_version = get_versions()["version"]
        roboprinter.printer_instance._logger.info("Initialized  Printer Jog, Octoprint Version is: " + str(self.octoprint_version))



    def jog(self,desired={'x':0, 'y':0, 'z':0, 'e':0 }, speed=None, relative=True, **kwargs):
        #use this location to check for version number then use the correct jog version
        if self.octoprint_version <= "1.2.9":
            #use the old jog
            for axis in desired:
                roboprinter.printer_instance._printer.jog(axis, desired[axis])

        elif self.octoprint_version >= "1.3.0":
            #use the new jog
            roboprinter.printer_instance._printer.jog(axes=desired, speed=speed, relative=relative)


printer_jog = Printer_Jog()