# -*- coding: utf-8 -*-
# @Author: Matt Pedler
# @Date:   2017-11-20 12:45:05
# @Last Modified by:   Matt Pedler
# @Last Modified time: 2018-01-28 14:54:20

#kivy
from kivy.uix.boxlayout import BoxLayout
from kivy.logger import Logger
from kivy.clock import Clock
from kivy.properties import StringProperty, NumericProperty

#RoboLCD
from RoboLCD.lcd.common_screens import Wizard_Screen_Controls
from pid_watcher import PID_Watcher
from RoboLCD import roboprinter
from RoboLCD.lcd.pconsole import pconsole
from RoboLCD.lcd.Language import lang

#python
import gc

class PID_Test_Screen(BoxLayout, Wizard_Screen_Controls):
    """docstring for PID_Test_Screen"""
    selected_heater = StringProperty('')
    title = StringProperty(lang.pack['PID_Tool']['Workflow']['Sub_Title'])
    P_text = StringProperty('')
    P_original = StringProperty('')
    I_text = StringProperty('')
    I_original = StringProperty('')
    D_text = StringProperty('')
    D_original = StringProperty('')
    temperature_text = StringProperty('')
    target_text = StringProperty('')
    current_test = NumericProperty(0)
    current_test_text = StringProperty('')

    _pid = {}
    _original_pid = {}

    def __init__(self, selected_tool, callback, failure_callback, debug=False):
        super(PID_Test_Screen, self).__init__()
        self.debug = debug
        self.changed_screen = False
        if int(selected_tool) == -1:
            self.selected_heater = lang.pack['PID_Tool']['Workflow']['Bed']
        elif int(selected_tool) == 0:
            self.selected_heater = lang.pack['PID_Tool']['Workflow']['Extruder1']
        elif int(selected_tool) == 1:
            self.selected_heater = lang.pack['PID_Tool']['Workflow']['Extruder2']

        #If there is only one extruder and the extruder is selected call it extruder.
        profile = roboprinter.printer_instance._settings.global_get(['printerProfiles', 'defaultProfile'])
        if 'extruder' in profile:
            extruder_count = int(profile['extruder']['count'])
        else:
            extruder_count = 1
        if extruder_count == 1 and int(selected_tool) == 0:
            self.selected_heater = lang.pack['PID_Tool']['Workflow']['Extruder']

        self.selected_tool = selected_tool

        self.title += self.selected_heater

        self.callback = callback
        self.failure_callback = failure_callback

        self.current_test_text = lang.pack['PID_Tool']['Workflow']['Waiting']
        self.temp_monitor = Clock.schedule_interval(self.monitor_temperature, 0.2)

        if self.selected_heater != lang.pack['PID_Tool']['Workflow']['Bed']:
            self._pid = pconsole.PID
        else:
            self._pid = pconsole.BPID
        self._original_pid = self._pid
        self.P_original = str(self._original_pid['P'])
        self.I_original = str(self._original_pid['I'])
        self.D_original = str(self._original_pid['D'])

        self.monitor_progress()

        # Check the debug state. If true, print out a list of instances of
        # PID_Test_Screen recognized by the garbage collector
        if self.debug:
            Logger.info("---> Checking PID_Test_Screen instances")
            obj_len = 0
            for obj in gc.get_objects():
                if isinstance(obj, PID_Test_Screen):
                    obj_len += 1
                    Logger.info("GC: " + str(obj))
            Logger.info("There are " + str(obj_len) + "PID_Test_Screen Objects active")

            # Print out the instance of this class. The name of the instance and
            # address in memory will be printed.
            Logger.info("SELF: " + str(self))

    def cleanup(self):
        #call extended cleanup methods
        super(PID_Test_Screen, self).cleanup()
        #cleanup PID_Watcher
        if self.pid_watcher != None:
            self.pid_watcher.cleanup()

        #cleanup bound methods
        self.failure_callback = ''
        self.callback = ''



    def monitor_progress(self):
            self.pid_watcher = PID_Watcher(self.finished, self.update_test, self.update_PID, self.failure_callback)

    def update_test(self):
        self.current_test += 1
        self.current_test_text = lang.pack['PID_Tool']['Workflow']['Stage1']+ str(self.current_test) + lang.pack['PID_Tool']['Workflow']['Stage2'] + lang.pack['PID_Tool']['Workflow']['Stage3']

    def update_PID(self, pid_dict):
        self.P_text = str(pid_dict['P'])
        self.I_text = str(pid_dict['I'])
        self.D_text = str(pid_dict['D'])
        self._pid = pid_dict

    def get_color(self, new, old):
        if float(new) != float(old):
            diff = float(new) - float(old)
            if diff > 0.00:
                difference = "[color=#008000]+{0:.2f}".format(diff) #green
            else:
                difference = "[color=#ff0000]{0:.2f}".format(diff) #red #if it is negative it will already come with a negative sign
    
            return str(difference)
        else:
            return ''

    def change_screen_event(self):
        self.changed_screen = True
        self.temp_monitor.cancel()

    def finished(self):
        if not self.changed_screen:
            self.temp_monitor.cancel()
            Clock.schedule_once(self.finished_after_5, 5) #hang out for five seconds then finish.

    def finished_after_5(self, *args, **kwargs):
        self.callback(self._pid)

    def failure_callback(self):
        if not self.changed_screen:
            self.failure_callback()

    def monitor_temperature(self, *args, **kwargs):
        temps = roboprinter.printer_instance._printer.get_current_temperatures()

        selected_tool = ''

        self.target_text = lang.pack['PID_Tool']['Workflow']['Target_Ext'] + lang.pack['PID_Tool']['Workflow']['Celsius']
        if int(self.selected_tool) == -1:
            selected_tool = 'bed'
            self.target_text = lang.pack['PID_Tool']['Workflow']['Target_Bed'] + lang.pack['PID_Tool']['Workflow']['Celsius']
        elif int(self.selected_tool) == 0:
            selected_tool = 'tool0'
        elif int(self.selected_tool) == 1:
            selected_tool = 'tool1'
        else:
            raise ValueError("Tool was not selected correctly: " + str(self.selected_tool))

        if selected_tool in temps and 'actual' in temps[selected_tool] :
            self.temperature_text = str(temps[selected_tool]['actual']) + lang.pack['PID_Tool']['Workflow']['Celsius']
        else:
            self.temperature_text = str(0) + lang.pack['PID_Tool']['Workflow']['Celsius']

class PID_Finish_Object(BoxLayout):
    """
    This is a custom object to put into the save portion of this wizard.
    This will show the PID in the spreadsheet form it was shown in the main portion of the wizard.
    """
    finished_text = StringProperty('')
    table_text = StringProperty('')
    P_text = StringProperty('')
    I_text = StringProperty('')
    D_text = StringProperty('')


    def __init__(self, finished_text, table_text, PID_values, **kwargs):
        super(PID_Finish_Object, self).__init__()
        self.finished_text = finished_text
        self.table_text = table_text
        self.P_text = str(PID_values['P'])
        self.I_text = str(PID_values['I'])
        self.D_text = str(PID_values['D'])
        
        



        
        