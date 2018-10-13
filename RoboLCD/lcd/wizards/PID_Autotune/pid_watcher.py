# -*- coding: utf-8 -*-
# @Author: Matt Pedler
# @Date:   2017-10-31 13:02:40
# @Last Modified by:   Matt Pedler
# @Last Modified time: 2018-01-30 12:31:35
import octoprint.printer
from RoboLCD import roboprinter
import time
from kivy.clock import Clock
from kivy.logger import Logger

class PID_Watcher(octoprint.printer.PrinterCallback, object):
    called_callback = False
    _pid = {'P': 0,
            'I': 0,
            'D': 0 }
    def __init__(self,callback, next_test_callback, PID_update_callback, timeout_callback, *args, **kwargs):
        super(PID_Watcher, self).__init__(*args, **kwargs)
        self.callback = callback
        self.next_test_callback = next_test_callback
        self.PID_update_callback = PID_update_callback
        self.timeout_callback = timeout_callback

        #register the observer with octoprint
        Logger.info("Registering Console Watcher")
        roboprinter.printer_instance._printer.register_callback(self)

    def cleanup(self):
        Logger.info("Unregistering Console Watcher through __del__!")
        #dereference all callbacks
        self.callback = ''
        self.next_test_callback = ''
        self.PID_update_callback = ''
        self.timeout_callback = ''

        #unregister if we have not already
        roboprinter.printer_instance._printer.unregister_callback(self)

        #delete self
        del self

    def on_printer_add_message(self, data):
        if data.find("ACTION COMPLETE!") != -1:
            Clock.schedule_once(self.callback_caller, 0.0)
        if data.find("bias") != -1:
            Clock.schedule_once(self.test_increment, 0.0)
        if data.find("PID Autotune failed!") != -1:
            Clock.schedule_once(self.timeout, 0.0)
        if data.find("Kp:") != -1:
            #analyze the line
            Logger.info(data)
            parsed_PID = self.parse_command(data)
            #merge and update
            self.PID = self.merge_dicts(self.PID, parsed_PID)
            Clock.schedule_once(self.PID_update, 0.0)
            

    def callback_caller(self, *args, **kwargs):
        if callable(self.callback):
            self.callback()
        roboprinter.printer_instance._printer.unregister_callback(self)
        self.cleanup()

    def test_increment(self, *args, **kwargs):
        if callable(self.next_test_callback):
            self.next_test_callback()

    def PID_update(self, *args, **kwargs):
        if callable(self.PID_update_callback):
            self.PID_update_callback(self.PID)

    def timeout(self, *args, **kwargs):
        if callable(self.timeout_callback):
            self.timeout_callback()
        roboprinter.printer_instance._printer.unregister_callback(self)
        self.cleanup()

    @property
    def PID(self):
        return self._pid

    @PID.setter
    def PID(self, value):
        self._pid = value


    def parse_command(self, data):
        return_dict = {}
        
        #remove all spaces
        data = data.replace(" ", "")
        data = data.replace("K","")
        data = data.replace(":","")
        
        acceptable_data = ['p', 'i', 'd']
        
        while [x for x in acceptable_data if (x in data)] != []: #this is the equivalent of if 'X' in data or 'Y' in data or 'Z' in data ect
            if data.find("p") != -1:
                var_data = self.scrape_data(data, "p")
                end_var_data = var_data.replace('p','')
                return_dict['P'] = float(end_var_data)    
                data = data.replace(var_data, '')
                
    
            elif data.find("i") != -1:
                var_data = self.scrape_data(data, "i")
                end_var_data = var_data.replace('i','')
                return_dict['I'] = float(end_var_data)    
                data = data.replace(var_data, '')
                
    
            elif data.find("d") != -1:
                var_data = self.scrape_data(data, "d")
                end_var_data = var_data.replace('d','')
                return_dict['D'] = float(end_var_data)    
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
        extra_chars = scraper.split()
        counter = 0
        acceptable_input = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '-', '.']
        for char in extra_chars:
            acceptable_input.append(char)
        for i in data:
            #print(i)
            counter += 1
            if i not in acceptable_input:
                break
            
        if counter == len(data):
            return len(data) #add the length of the scraper back in
        else:
            return counter -1

    def merge_dicts(self, *dict_args):
        result = {}
        for dictionary in dict_args:
            result.update(dictionary)
        return result