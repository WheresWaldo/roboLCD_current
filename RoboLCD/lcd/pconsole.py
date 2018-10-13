# -*- coding: utf-8 -*-
# @Author: Matt Pedler
# @Date:   2017-10-19 12:47:23
# @Last Modified by:   Matt Pedler
# @Last Modified time: 2017-12-05 13:46:23
import octoprint.printer
from RoboLCD import roboprinter
import re
import signal
import time


class PConsole(octoprint.printer.PrinterCallback, object):



    position = []
    position_ready = False
    #dictionary for eeprom
    eeprom_ready = False

    _home_offset = {}
    _probe_offset = {}
    _feed_rate = {}
    _PID = {}
    _BPID = {}
    _steps_per_unit = {}
    _accelerations = {}
    _max_accelerations = {}
    _advanced_variables = {}
    _linear_advanced = {}

    #TODO Implement hotend offset
    hotend_offset = {}
    #/TODO

    counter = 0
    t_counter = 2
    temperature = {}
    sent_M114 = False
    cur_time = 0

    sent_tool_change = False
    tool_change_done = False

    busy = False
    temperature = {
                    'tool1': 0,
                    'tool1_desired': 0,
                    'tool2': 0,
                    'tool2_desired': 0,
                    'bed': 0,
                    'bed_desired': 0,
                    }

    def __init__(self, *args, **kwargs):
        super(PConsole, self).__init__(*args, **kwargs)
        self.registered_callbacks = {}

    def on_printer_add_message(self, data):

        ##roboprinter.printer_instance._logger.info(data)

        if data.find("echo:busy: processing") != -1:
            self.busy = True
        else:
            self.busy = False
        
        find_data = ['M92', 'M203', 'M201', 'M204', 'M205', 'M206', 'M218', 'M301', 'M304', 'M851', 'Z Offset', 'M900']

        acceptable_finds = {
                            'M92': self.find_M92,
                            'M203': self.find_M203,
                            'M201': self.find_M201,
                            'M204': self.find_M204,
                            'M205': self.find_M205,
                            'M206': self.find_M206,
                            'M218': self.find_M218,
                            'M301': self.find_M301,
                            'M304': self.find_M304,
                            'M851': self.find_M851,
                            'Z Offset': self.find_zoffset,
                            'M900': self.find_M900,

        }

        for query in find_data:
            found = data.find(query)

            if found != -1:
                #execute dictionary function
                acceptable_finds[query](data)
                break        

        #Disconnect and reconnect if Marlin stops because of bed heater issues
        printer_bed_error = 'Error:MINTEMP triggered, system stopped! Heater_ID: bed'
        printer_bed_error2 = "Error:Heating failed, system stopped! Heater_ID: bed"
        general_error = "Error:Printer halted. kill() called!"
        connection_error = "Error:No Line Number with checksum, Last Line: 0"

        if re.match(printer_bed_error, data) or re.match(printer_bed_error2,data) or re.match(general_error, data) or re.match(connection_error,data):
            roboprinter.printer_instance._logger.info("Disconnecting")
            roboprinter.printer_instance._printer.disconnect()
            time.sleep(2)
            roboprinter.printer_instance._logger.info("Reconnecting")
            roboprinter.printer_instance._printer.connect()

        #Find out if octoprint is not reporting a bed temp loss
        model = roboprinter.printer_instance._settings.get(['Model'])
        if model == "Robo R2":
            
            def find_temps():
                ext1 = -1
                ext1_dual = -1
                ext2 = -1
                bed = -1
                if data.find('T:') != -1:
                    ext1 = data.find('T:')
                if data.find('T0:') != -1:
                    ext_dual = data.find('T0:')
                if data.find('T1:') != -1:
                    ext2 = data.find('T1:')
                if data.find('B:') != -1:
                    bed = data.find('B:')

                #Dual Extrusion R2
                if ext1_dual != -1 and ext2 != -1 and bed != -1:
                    bed_s = temp[bed:ext1_dual]
                    bed = extract_data(bed_s)

                    self.temperature['bed'] = bed['current']
                    self.temperature['bed_desired'] = bed['desired']

                    ext1_s = temp[ext1_dual+2:ext2]
                    tool1 = extract_data(ext1_s)

                    self.temperature['tool1'] = tool1['current']
                    self.temperature['tool1_desired'] = tool1['desired']

                    ext2_s = temp[ext2+2:temp.find('@')]
                    tool2 = extract_data(ext2_s)

                    self.temperature['tool2'] = tool2['current']
                    self.temperature['tool2_desired'] = tool2['desired']


                    

                #Single Nozzle R2
                elif ext1 != -1 and bed != -1:
                    ext1_s = data[ext1:bed]
                    tool1 = extract_data(ext1_s)

                    self.temperature['tool1'] = tool1['current']
                    self.temperature['tool1_desired'] = tool1['desired']

                    bed_s = data[bed:data.find('@')]
                    bed = extract_data(bed_s)

                    self.temperature['bed'] = bed['current']
                    self.temperature['bed_desired'] = bed['desired']

                else:
                    roboprinter.printer_instance._logger.info("Model is R2 and we cannot find bed and extruder!!!")
                    roboprinter.printer_instance._logger.info(data)

            def extract_data(temp_string):
                temperature =  "[+-]?\d+(?:\.\d+)?"
                current_temp = re.findall(temperature, temp_string)

                temp = {
                        'current':current_temp[0],
                        'desired':current_temp[1]
                       }
                return temp

            #disconnect if the bed reports a negative number two times in a row
            if data.find('T:') != -1 and data.find('B:') != -1:
                
                find_temps()

                if float(self.temperature['bed']) < 0:
                    self.t_counter -= 1
                    roboprinter.printer_instance._logger.info(str(self.t_counter))
                    if self.t_counter == 0:
                        roboprinter.printer_instance._logger.info("Shutting down")
                        roboprinter.printer_instance._printer.disconnect()
                        self.t_counter = 2



        #get the position
        if self.sent_M114:
            p = "X:([-0-9.00]+)Y:([-0-9.00]+)Z:([-0-9.00]+)E:([-0-9.00]+)CountX:([-0-9]+)Y:([-0-9]+)Z:([-0-9]+)"
            temp_pos = re.findall(p, data.replace(" ", ""))
            if temp_pos != []:
                #only return a time if the function actually gets data
                finished_time = (time.time() - self.cur_time) * 1000
                roboprinter.printer_instance._logger.info("position getting it in " + str(finished_time) + " ms")

                self.position = temp_pos[0]
                #roboprinter.printer_instance._logger.info('Position Update')
                #roboprinter.printer_instance._logger.info(str(self.position))
                self.position_ready = True
                

        #detect tool change
        if self.sent_tool_change:
            p = "Active Extruder"
            if data.find(p) != -1:
                self.tool_change_done = True

    def parse_M_commands(self, data, command):
        return_dict = {}
        #cut M command
        data = data.replace(command, "")
        #remove all spaces
        data = data.replace(" ", "")

        
        acceptable_data = ['X', 'Y', 'Z', 'E', 'P', 'I', 'D', 'R', 'T' , 'S', 'B', 'K']
        
        while [x for x in acceptable_data if (x in data)] != []: #this is the equivalent of if 'X' in data or 'Y' in data or 'Z' in data ect
            if data.find("X") != -1:
                var_data = self.scrape_data(data, "X")
                end_var_data = var_data.replace('X','')
                return_dict['X'] = float(end_var_data)    
                data = data.replace(var_data, '')
                
    
            elif data.find("Y") != -1:
                var_data = self.scrape_data(data, "Y")
                end_var_data = var_data.replace('Y','')
                return_dict['Y'] = float(end_var_data)    
                data = data.replace(var_data, '')
                
    
            elif data.find("Z") != -1:
                var_data = self.scrape_data(data, "Z")
                end_var_data = var_data.replace('Z','')
                return_dict['Z'] = float(end_var_data)    
                data = data.replace(var_data, '')
                
    
            elif data.find("E") != -1 and data.find("T0") != -1 and command != "M205":
                var_data = self.scrape_data(data, "E")
                end_var_data = var_data.replace('E', '')
                return_dict['T0 E'] = float(end_var_data)
                data = data.replace(var_data, '')
                data = data.replace("T0", '')
                
    
            elif data.find("E") != -1 and data.find("T1") != -1 and command != "M205":
                var_data = self.scrape_data(data, "E")
                end_var_data = var_data.replace('E', '')
                return_dict['T1 E'] = float(end_var_data)
                data = data.replace(var_data, '')
                data = data.replace("T1", '')
                
    
            elif data.find("E") != -1 :
                var_data = self.scrape_data(data, "E")
                end_var_data = var_data.replace('E', '')
                return_dict['E'] = float(end_var_data)    
                data = data.replace(var_data, '')
                

            elif data.find("P") != -1:
                var_data = self.scrape_data(data, "P")
                end_var_data = var_data.replace('P', '')
                return_dict['P'] = float(end_var_data)    
                data = data.replace(var_data, '')
                

            elif data.find("I") != -1:
                var_data = self.scrape_data(data, "I")
                end_var_data = var_data.replace('I', '')
                return_dict['I'] = float(end_var_data)    
                data = data.replace(var_data, '')
                

            elif data.find("D") != -1:
                var_data = self.scrape_data(data, "D")
                end_var_data = var_data.replace('D', '')
                return_dict['D'] = float(end_var_data)    
                data = data.replace(var_data, '')
                

            elif data.find("R") != -1:
                var_data = self.scrape_data(data, "R")
                end_var_data = var_data.replace('R','')
                return_dict['R'] = float(end_var_data)    
                data = data.replace(var_data, '')
                

            elif data.find("T") != -1:
                var_data = self.scrape_data(data, "T")
                end_var_data = var_data.replace('T','')
                return_dict['T'] = float(end_var_data)    
                data = data.replace(var_data, '')
                

            elif data.find("B") != -1:
                var_data = self.scrape_data(data, "B")
                end_var_data = var_data.replace('B','')
                return_dict['B'] = float(end_var_data)    
                data = data.replace(var_data, '')
                

            elif data.find("S") != -1:
                var_data = self.scrape_data(data, "S")
                end_var_data = var_data.replace('S','')
                return_dict['S'] = float(end_var_data)    
                data = data.replace(var_data, '')

            elif data.find("K") !=-1:
                var_data = self.scrape_data(data, "K")
                end_var_data = var_data.replace('K','')
                return_dict['K'] = float(end_var_data)    
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
        acceptable_input = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '-', '.', scraper]
        for i in data:
            #print(i)
            counter += 1
            if i not in acceptable_input:
                break
            
        if counter == len(data):
            return len(data)
        else:
            return counter -1
    def merge_dicts(self, *dict_args):
        result = {}
        for dictionary in dict_args:
            result.update(dictionary)
        return result

    def dict_logger(self, dictionary, indent = 0):
        indent_string = ""
        for x in range(indent):
            indent_string += "|"

        for item in dictionary:
            if type(dictionary[item]) is dict:
                if indent == 0:
                    roboprinter.printer_instance._logger.info("")
                roboprinter.printer_instance._logger.info(indent_string + item + ":")
                self.dict_logger(dictionary[item], indent=(indent+1))
            else:
                report_string = indent_string + str(item) + ": " + str(dictionary[item])
                roboprinter.printer_instance._logger.info(report_string)
    
    #Steps Per Unit
    def find_M92(self, data):
        #roboprinter.printer_instance._logger.info("M92 "+ str(self.counter))
        self.steps_per_unit = self.merge_dicts(self.steps_per_unit,self.parse_M_commands(data, 'M92'))
        finished_time = (time.time() - self.cur_time) * 1000
        roboprinter.printer_instance._logger.info("M92 getting it in " + str(finished_time) + " ms")

    #Maximum Feed Rate
    def find_M203(self, data):
        #roboprinter.printer_instance._logger.info("M203 "+ str(self.counter))
        self.feed_rate = self.merge_dicts(self.feed_rate, self.parse_M_commands(data, "M203"))
        finished_time = (time.time() - self.cur_time) * 1000
        roboprinter.printer_instance._logger.info("M203 getting it in " + str(finished_time) + " ms")

    #Maximun Acceleration
    def find_M201(self, data):
        self.max_accelerations = self.merge_dicts(self.max_accelerations, self.parse_M_commands(data, "M201"))
        finished_time = (time.time() - self.cur_time) * 1000
        roboprinter.printer_instance._logger.info("M201 getting it in " + str(finished_time) + " ms")

    #Accelerations
    def find_M204(self, data):
        #roboprinter.printer_instance._logger.info("M204 "+ str(self.counter))
        
        self.accelerations = self.merge_dicts(self.accelerations, self.parse_M_commands(data, "M204"))
        finished_time = (time.time() - self.cur_time) * 1000
        roboprinter.printer_instance._logger.info("M204 getting it in " + str(finished_time) + " ms")

    #advanced variables
    def find_M205(self, data):
        #roboprinter.printer_instance._logger.info("M205 "+ str(self.counter))
        
        self.advanced_variables = self.merge_dicts(self.advanced_variables, self.parse_M_commands(data, "M205"))
        finished_time = (time.time() - self.cur_time) * 1000
        roboprinter.printer_instance._logger.info("M205 getting it in " + str(finished_time) + " ms")

    #home offset
    def find_M206(self, data):
        self.home_offset = self.merge_dicts(self.home_offset, self.parse_M_commands(data, "M206"))
        finished_time = (time.time() - self.cur_time) * 1000
        roboprinter.printer_instance._logger.info("M206 getting it in " + str(finished_time) + " ms")

    #hotend offset
    def find_M218(self, data):
        self.hotend_offset = self.merge_dicts(self.hotend_offset, self.parse_M_commands(data, "M218"))
        finished_time = (time.time() - self.cur_time) * 1000
        roboprinter.printer_instance._logger.info("M118 getting it in " + str(finished_time) + " ms")


    #PID settings
    def find_M301(self, data):
        #roboprinter.printer_instance._logger.info("M301 " + data)
        self.PID = self.merge_dicts(self.PID, self.parse_M_commands(data, 'M301'))
        finished_time = (time.time() - self.cur_time) * 1000
        roboprinter.printer_instance._logger.info("M301 getting it in " + str(finished_time) + " ms")

    def find_M304(self, data):
        #roboprinter.printer_instance._logger.info("M301 "+ str(self.counter))
        
        self.BPID = self.merge_dicts(self.BPID, self.parse_M_commands(data, "M304"))
        finished_time = (time.time() - self.cur_time) * 1000
        roboprinter.printer_instance._logger.info("M304 getting it in " + str(finished_time) + " ms")

    #Zoffset
    def find_M851(self, data):

        self.probe_offset = self.merge_dicts(self.probe_offset, self.parse_M_commands(data, "M851"))
        finished_time = (time.time() - self.cur_time) * 1000
        roboprinter.printer_instance._logger.info("M851 getting it in " + str(finished_time) + " ms")
        #EEPROM is ready
        self.eeprom_ready = True

    #Zoffset update
    def find_zoffset(self,data):
        data = data.replace('Z Offset', "M851") #make it an M851 command
        self.probe_offset = self.merge_dicts(self.probe_offset, self.parse_M_commands(data, "M851"))
        finished_time = (time.time() - self.cur_time) * 1000
        roboprinter.printer_instance._logger.info("ZOffset getting it in " + str(finished_time) + " ms")

    #Linear Advanced M900
    def find_M900(self, data):
        #roboprinter.printer_instance._logger.info("M301 " + data)
        self.linear_advanced = self.merge_dicts(self.linear_advanced, self.parse_M_commands(data, 'M900'))
        finished_time = (time.time() - self.cur_time) * 1000
        roboprinter.printer_instance._logger.info("M900 getting it in " + str(finished_time) + " ms")

    def query_eeprom(self):
        self.cur_time = time.time()
        roboprinter.printer_instance._printer.commands('M501')

    #this will pause all processing until we get the EEPROM. Not recommended to use unless you need updates to the EEPROM
    def get_eeprom(self):
        self.eeprom_ready = False
        self.cur_time = time.time()
        roboprinter.printer_instance._printer.commands('M501')

        while (self.eeprom_ready == False):
            pass

        self.eeprom_ready = False

        return 

    def generate_eeprom(self):
        self.eeprom_ready = False
        roboprinter.printer_instance._printer.commands('M501')

    def get_old_eeprom(self):
        pass #deprecated

    def get_position(self):

        if not self.busy:
            self.sent_M114 = True
            self.cur_time = time.time()
            roboprinter.printer_instance._printer.commands('M114')
            
            while (self.position_ready == False):
                pass
    
            self.position_ready = False
            self.sent_M114 = False
            return self.position
        else:
            return False

    def change_tool(self, tool):
        acceptable_tools = {'tool0': "T0",
                            'tool1': "T1"
                            }
        if not self.busy:
            if tool in acceptable_tools:
                self.sent_tool_change = True
                roboprinter.printer_instance._printer.commands(acceptable_tools[tool])

                while self.tool_change_done == False:
                    pass

                self.tool_change_done = False
                self.sent_tool_change = False
                return True
            else:
                return False
        else:
            return False
    
        
    def initialize_eeprom(self):
        pass #deprecated

    #let classes set up ovservers for any variable
    def register_observer(self, command, callback):

        #This is a list for recognizing valid callbacks
        pconsole_values = [ 'M206', 
                            'M851',
                            'M203',
                            'M301',
                            'M304',
                            'M92',
                            'M204',
                            'M201',
                            'M205',
                            'M900',
                            ]

        if command in pconsole_values:
            if command in self.registered_callbacks and type(self.registered_callbacks[command]) == list:
                self.registered_callbacks[command].append(callback)
                roboprinter.printer_instance._logger.info("Added a callback for command: " + str(command) + " ID: " + str(id(callback)))
            else:
                self.registered_callbacks[command] = [callback]
                roboprinter.printer_instance._logger.info("Added first callback for command: " + str(command) + " ID: " + str(id(callback)))
            return True
        roboprinter.printer_instance._logger.info("Failed to add callback for command: " + str(command) + " ID: " + str(id(callback)))
        return False

    def unregister_observer(self, command, callback):
        #This is a list for recognizing valid callbacks
        pconsole_values = [ 'M206', 
                            'M851',
                            'M203',
                            'M301',
                            'M304',
                            'M92',
                            'M204',
                            'M201',
                            'M205',
                            'M900',
                            ]
        if command in pconsole_values:
            #for every callback in the command 
            if callback in self.registered_callbacks[command]:
                self.registered_callbacks[command].remove(callback)
                roboprinter.printer_instance._logger.info("Deleted Callback for command: " + str(command) + " ID: " + str(id(callback)))
                return True
        roboprinter.printer_instance._logger.info("Failed to remove callback for command: " + str(command) + " ID: " + str(id(callback)))
        return False

    #use the var_id to find callbacks, then callback all callbacks with the value as the only argument
    def observer_caller(self, var_id, value):
        if var_id in self.registered_callbacks:
            #import json
            #roboprinter.printer_instance._logger.info(str(self.registered_callbacks))
            for callback in self.registered_callbacks[var_id]:
                callback(value)


    ############################################################################################################################
    #                                               PConsole Variable Observers                                                #
    ############################################################################################################################

    @property
    def home_offset(self):
        return self._home_offset

    @home_offset.setter
    def home_offset(self, value):
        self._home_offset = value
        var_id = 'M206'
        self.observer_caller(var_id, self._home_offset)
        
    @property
    def probe_offset(self):
        return self._probe_offset

    @probe_offset.setter
    def probe_offset(self, value):
        self._probe_offset = value
        var_id = 'M851'
        self.observer_caller(var_id, self._probe_offset)

    @property
    def feed_rate(self):
        return self._feed_rate

    @feed_rate.setter
    def feed_rate(self, value):
        self._feed_rate = value
        var_id = 'M203'
        self.observer_caller(var_id, self._feed_rate)

    @property
    def PID(self):
        return self._PID

    @PID.setter
    def PID(self, value):
        self._PID = value
        var_id = 'M301'
        self.observer_caller(var_id, self._PID)

    @property
    def BPID(self):
        return self._BPID

    @BPID.setter
    def BPID(self, value):
        self._BPID = value
        var_id = 'M304'
        self.observer_caller(var_id, self._BPID)

    @property
    def steps_per_unit(self):
        return self._steps_per_unit

    @steps_per_unit.setter
    def steps_per_unit(self, value):
        self._steps_per_unit = value
        var_id = 'M92'
        self.observer_caller(var_id, self._steps_per_unit)

    @property
    def accelerations(self):
        return self._accelerations

    @accelerations.setter
    def accelerations(self, value):
        self._accelerations = value
        var_id = 'M204'
        self.observer_caller(var_id, self._accelerations)

    @property
    def max_accelerations(self):
        return self._max_accelerations

    @max_accelerations.setter
    def max_accelerations(self, value):
        self._max_accelerations = value
        var_id = 'M201'
        self.observer_caller(var_id, self._max_accelerations)

    @property
    def advanced_variables(self):
        return self._advanced_variables

    @advanced_variables.setter
    def advanced_variables(self, value):
        self._advanced_variables = value
        var_id = 'M205'
        self.observer_caller(var_id, self._advanced_variables)

    @property
    def linear_advanced(self):
        return self._linear_advanced

    @linear_advanced.setter
    def linear_advanced(self, value):
        self._linear_advanced = value
        var_id = 'M900'
        self.observer_caller(var_id, self._linear_advanced)

    def join_EEPROM(self, join_list = []):
        catcher_returns = {}
        return_list = []
        def catcher(command, value):
            roboprinter.printer_instance._logger.info("Command: " + str(command) + " Returned: " + str(value))
            catcher_returns[command] = value
            
        def monitor_returns():
            import time
            returns_complete = False
            roboprinter.printer_instance._logger.info("Thread starting")
            while not returns_complete:
                if len([x for x in join_list if (x in catcher_returns)]) == len(join_list):
                    for command in join_list:
                        return_list.append(catcher_returns[command])
                    returns_complete = True
                    roboprinter.printer_instance._logger.info("Returns Complete")
                    break
                else:
                    time.sleep(1)
            
            return return_list

        for command in join_list:
            EEPROM_Catcher(command, catcher)

        pconsole.query_eeprom()
        
        #start thread to monitor asynchronus task
        import threading
        monitor = threading.Thread(target = monitor_returns)
        monitor.start()
        monitor.join()

        return return_list

        

class EEPROM_Catcher(object):
    """docstring for EEPROM_Catcher"""
    def __init__(self, command, callback):
        super(EEPROM_Catcher, self).__init__()
        self.command = command
        self.callback = callback
        self.register_catcher()

    def __del__(self):
        pconsole.unregister_observer(self.command, self.catcher)

    def register_catcher(self):
        pconsole.register_observer(self.command, self.catcher)

    def catcher(self, value):
        self.callback(self.command, value)
        self.__del__()
        
        

pconsole = PConsole()
