# -*- coding: utf-8 -*-
# @Author: Matt Pedler
# @Date:   2017-10-31 13:02:40
# @Last Modified by:   Matt Pedler
# @Last Modified time: 2017-11-08 11:23:13
import octoprint.printer
from RoboLCD import roboprinter
import time
from kivy.clock import Clock
from kivy.logger import Logger

class Console_Watcher(octoprint.printer.PrinterCallback, object):
    called_callback = False
    def __init__(self,callback, *args, **kwargs):
        super(Console_Watcher, self).__init__(*args, **kwargs)
        self.callback = callback

        #register the observer with octoprint
        Logger.info("Registering Console Watcher")
        roboprinter.printer_instance._printer.register_callback(self)
    def __del__(self):
        Logger.info("Unregistering Console Watcher through __del__!")
        roboprinter.printer_instance._printer.unregister_callback(self)

    def on_printer_add_message(self, data):
        if data.find("Bed") != -1:
            self.callback(self.parse_M_commands(data, "Bed"))
            self.__del__()

    def parse_M_commands(self, data, command):
        return_dict = {}
        #cut M command
        data = data.replace(command, "")
        #remove all spaces
        data = data.replace(" ", "")

        
        acceptable_data = ['Z']
        
        while [x for x in acceptable_data if (x in data)] != []: #this is the equivalent of if 'X' in data or 'Y' in data or 'Z' in data ect
            
            if data.find("Z") != -1:
                var_data = self.scrape_data(data, "Z")
                end_var_data = var_data.replace('Z','')
                end_var_data = end_var_data.replace(':','')
                return_dict['Z'] = float(end_var_data)    
                data = data.replace(var_data, '')
                

        return return_dict

    def scrape_data(self, data, scraper):
        start_pos = data.find(scraper)
    
        if start_pos == -1:
            print("Cannot find data for scraper: " + str(scraper))
            return False
    
        end_pos = self.find_next_space(data[start_pos:len(data)], scraper)
    
        scraped = data[start_pos:start_pos + end_pos]
    
        return scraped
        

    def find_next_space(self, data, scraper):
        counter = 0
        acceptable_input = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '-', '.', ':', scraper]
        for i in data:
            #print(i)
            counter += 1
            if i not in acceptable_input:
                break
            
        if counter == len(data):
            return len(data)
        else:
            return counter -1