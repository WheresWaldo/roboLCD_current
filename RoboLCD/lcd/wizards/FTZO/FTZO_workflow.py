# -*- coding: utf-8 -*-
# @Author: Matt Pedler
# @Date:   2017-10-27 11:32:59
# @Last Modified by:   Matt Pedler
# @Last Modified time: 2018-01-31 17:46:20
#kivy
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.logger import Logger
from kivy.properties import ObjectProperty, StringProperty, BooleanProperty, NumericProperty, ListProperty
from kivy.clock import Clock

#RoboLCD
from RoboLCD import roboprinter
from RoboLCD.lcd.printer_jog import printer_jog
from RoboLCD.lcd.common_screens import Button_Screen, Picture_Button_Screen
from RoboLCD.lcd.common_screens import Wait_Screen, Modal_Question, Image_on_Button_Screen, Picture_Image_on_Button_Screen, Temperature_Wait_Screen, Title_Picture_Image_on_Button_Screen, Extruder_Selector
from RoboLCD.lcd.pconsole import pconsole
from RoboLCD.lcd.connection_popup import Error_Popup, Warning_Popup
from RoboLCD.lcd.wizards.FTZO.FTZO_screens import Update_Offset, FTZO_Options


#python
from functools import partial
import time
import inspect
import gc
import weakref
class FTZO_workflow(object):
    """docstring for FTZO_workflow"""

    #variables for editing the Z-Offset and the Z-Offset options. 
    EZO_screen = None
    EZO_options = None
    _selected_tool = 'tool0'

    def __init__(self, dual, selected_tool, temps, callback, back_button, debug=False):
        super(FTZO_workflow, self).__init__()
        self.bb = back_button
        self.debug = False
        self.options = None
        self.wait_screen = None
        #start up wait screen so user does not see a frozen screen
        self.show_wait_screen()

        #Extruder variables
        self.dual = dual #this variable will alter the option layout
        self.temps = temps #This variable holds a dictionary of the temps for EXT1, EXT2, and BED temperature
        self.selected_tool = selected_tool #setting this variable will automatically select the tool and apply the temp for that tool        
        
        self.line_lock = False
        self.model = roboprinter.printer_instance._settings.get(['Model'])
        self.set_mode("R2L")#Modes are L2R and R2L
        self.prepared_printer = False
        self.user_back_out = False
        self.pconsole_waiter = None
        
        #save the exit callback
        self.callback = callback
        if not self.debug:
            Clock.schedule_once(self.prepare_for_lines, 2)
        else:
            Clock.schedule_once(self.debug_prepare, 2)

        # Check the debug state. If true, print out a list of instances of
        # FTZO_workflow recognized by the garbage collector
        if self.debug:
            Logger.info("---> Checking FTZO_workflow instances")
            obj_len = 0
            for obj in gc.get_objects():
                if isinstance(obj, FTZO_workflow):
                    obj_len += 1
                    Logger.info("GC " + str(obj))
            Logger.info("There are " + str(obj_len) + " FTZO_workflow Objects active")

            # Print out the instance of this class. The name of the instance and
            # address in memory will be printed.
            Logger.info("SELF: " + str(self))

    def cleanup(self):
        Logger.info("Deleting: FTZO_workflow")
        del self.callback
        if self.options != None:
            self.options.cleanup()
        if self.wait_screen != None:
            self.wait_screen.cleanup()
        self.bb = ''
        del_list = []
        for self_var in self.__dict__:
            del_list.append(self_var)
            self.__dict__[self_var] = ''
        for self_var in del_list:
            #Logger.info("Deleting " + str(self_var))
            del self.__dict__[self_var]
        #uncomment this if you want to see the refferers
        # Logger.info("---> Printing referrers of FTZO_workflow")
        # gc.collect()
        # for referer in gc.get_referrers(self):
        #     Logger.info(referer)
        # Logger.info("---> Done printing referrers of FTZO_workflow")
        del self
              
    def set_mode(self, mode):
        '''
        Set mode will be used to automatically select the best settings based upon the Attached printers bed size.
        This has an unfortunate requirement of the bed size being defined in the printer profile.

        This algorith will set an offset of 10mm to each of the sides
        '''
        self.corner = mode #set the appropriate mode

        #get bed dimensions
        bed_x = roboprinter.printer_instance._settings.global_get(['printerProfiles','defaultProfile', 'volume','width'])
        bed_y = roboprinter.printer_instance._settings.global_get(['printerProfiles','defaultProfile', 'volume','depth'])
        z_height = roboprinter.printer_instance._settings.global_get(['printerProfiles','defaultProfile', 'volume','height'])
        offset = 10.00 #offset of 10mm from Max X/Y dimensions
        self.drop_amount = z_height / 2.00

        if mode == "L2R":
            #left corner is (0, Max Y)
            self.start_pos_x = offset  
            self.start_pos_y = bed_y - offset 
            self.travel_amount = offset #bed Y max - 10mm
            self.max_x_travel = bed_x - offset #bed x max - 10mm
            

        elif mode == "R2L":
            #right corner is (x_max, y_max) 
            self.start_pos_x = bed_x - offset #Bed X max - 10mm
            self.start_pos_y = bed_y - offset #Y stays the same for the back of the bed
            self.travel_amount = offset #travel max Y - 10 mm
            self.max_x_travel = offset # travel all the way to the left
           

        elif mode == "CIRCLE":
            self.start_pos_x = bed_x - offset #Start at bed X max
            self.start_pos_y = bed_y / 2.00 #start in the middle of max Y
            self.travel_amount = 0.00 #unused in circles, but needs to be defined
            self.max_x_travel = (bed_x / 2) + 25.00 #Smallest circle can be a circle with a radius of 25mm (25mm ~= 1 inch)
            
        self.mode = {
            'corner': self.corner, #This variable is just what mode we are in. not just the corner anymore
            'start_pos_x': self.start_pos_x,
            'start_pos_y': self.start_pos_y,
            'travel_amount': self.travel_amount,
            'max_x_travel' : self.max_x_travel,
            'drop_amount': self.drop_amount,
            'x': self.start_pos_x
        }

        if self.EZO_screen != None:
            self.EZO_screen.update_mode(self.mode)
            Logger.info("New Corner Picked########")
            #prepare the printer
            roboprinter.printer_instance._printer.commands('G1 X'+ str(self.start_pos_x) + ' Y'+ str(self.start_pos_y) + ' F3000') # go to first corner
            roboprinter.printer_instance._printer.commands('G1 Z5') #bring bed close to the nozzle
    
           

    #debug prepare for lines
    def debug_prepare(self, *args, **kwargs):
        def fire_commands(*args, **kwargs):
            roboprinter.printer_instance._printer.commands('M118 ACTION COMPLETE!') 
        Clock.schedule_once(fire_commands, 3)

    #Prepare the printer for the Wizard
    def prepare_for_lines(self, *args, **kwargs):
        #Prepare the printer for the wizard
        pconsole.query_eeprom() #getting the EEPROM for a seperate process
        roboprinter.printer_instance._printer.commands('G36') #Robo's Autolevel
        roboprinter.printer_instance._printer.commands('G1 X'+ str(self.start_pos_x) + ' Y'+ str(self.start_pos_y) + ' F3000') # go to first corner
        roboprinter.printer_instance._printer.commands('G1 Z5') #bring bed close to the nozzle
        roboprinter.printer_instance._printer.commands('M114') #process position
        roboprinter.printer_instance._printer.commands('M118 ACTION COMPLETE!') 

    #Show the wait screen
    def show_wait_screen(self, *args, **kwargs):
        self.wait_screen = Wait_Screen(self.check_temp, 
                             roboprinter.lang.pack['FT_ZOffset_Wizard']['Prepare_Lines']['Sub_Title'] , 
                             roboprinter.lang.pack['FT_ZOffset_Wizard']['Prepare_Lines']['Body'],
                             watch_action=True)
        title = roboprinter.lang.pack['FT_ZOffset_Wizard']['Prepare_Lines']['Title']
        self.wait_screen.update = self.wait_screen_skip_action
        self.wait_screen.change_screen_actions = self.user_backed_out

        self.bb.make_screen(self.wait_screen,
                            title,
                            option_function='no_option')

    def wait_screen_skip_action(self):
        Logger.info("Prepare Printer back action! Killing heaters and fans")
        roboprinter.printer_instance._printer.commands('M104 S0')
        roboprinter.printer_instance._printer.commands('M140 S0')
        self.bb.back_function_flow()

    def user_backed_out(self, *args, **kwargs):
        roboprinter.printer_instance._printer.commands('M104 S0')
        roboprinter.printer_instance._printer.commands('M140 S0')
        self.user_back_out = True
        if self.pconsole_waiter != None:
            Logger.info("Attempting to kill waiter in the great hall with the candle stick")
            self.pconsole_waiter.cancel()

    #wait for temperatures
    def check_temp(self, *args, **kwargs):
        Logger.info("Checking Temp")
        temps = roboprinter.printer_instance._printer.get_current_temperatures()

        #find the temperature
        extruder_temp = 0 #initialize the variable so the function does not break.
        if self.selected_tool in temps:
            extruder_temp = temps[self.selected_tool]['actual']
        else:
            Logger.info("Cannot find temperature for: " + str(self.selected_tool))

        if extruder_temp >= self.temps[self.selected_tool]:
            self.show_EZO_screen()
        else:
            if not self.debug:
                self.temperature_wait_screen() 
            else:
                self.show_EZO_screen()

    def temperature_wait_screen(self, *args):
        title = roboprinter.lang.pack['ZOffset_Wizard']['Wait']
        back_destination = roboprinter.robo_screen()

        #get wait screen
        from RoboLCD.lcd.common_screens import Temperature_Wait_Screen

        #wait for the temperature to change, then go back to the EZO screen
        layout = Temperature_Wait_Screen(self.show_EZO_screen, tool_select=self.selected_tool)
        layout.update = self.wait_screen_skip_action
        layout.change_screen_actions = self.turn_off_heaters
        title= roboprinter.lang.pack['FT_ZOffset_Wizard']['Temp_Wait_Title']
        self.bb.make_screen(layout, 
                                                title,
                                                option_function='no_option')

        Logger.info("Temperature Wait Screen Activated")

    def turn_off_heaters(self):
        roboprinter.printer_instance._printer.commands('M104 S0')
        roboprinter.printer_instance._printer.commands('M140 S0')


    def show_EZO_screen(self, *args, **kwargs):

        #make the screen if it isnt already made
        if self.EZO_screen == None:
            self.EZO_screen = Update_Offset(self.mode, self.bb)
            self.bb.make_screen(self.EZO_screen,
                                                    self.EZO_screen.title,
                                                    option_function=self.show_EZO_options,
                                                    option_icon="Icons/Files_Icons/Hamburger_lines.png")
        else:
            self.EZO_screen.update_mode(self.mode)
            if self.bb.does_screen_exist(self.EZO_screen.title):
                self.bb.go_back_to_screen_with_title(self.EZO_screen.title)
            else:
                #reduntant protection. This should never fire
                Logger.info("EZO screen did not exist. cannot go back to screen. Re making EZO Screen")
                self.EZO_screen = None
                self.show_EZO_screen()


    def show_EZO_options(self):
        if self.options == None:
            self.options = FTZO_Options(self.dual, self.mode, self.set_mode, self.selected_tool_get_and_set, self.save_offset, self.callback, self.bb)
        else:
            self.options.cleanup()
            self.options = FTZO_Options(self.dual, self.mode, self.set_mode, self.selected_tool_get_and_set, self.save_offset, self.callback, self.bb)

        self.bb.make_screen(self.options,
                            roboprinter.lang.pack['FT_ZOffset_Wizard']['Options']['Title'],
                            option_function="no_option")

    #this function is passed to another class to use to update this property variable as we cannot share the properties getter and setter directly
    def selected_tool_get_and_set(self, value=''):
        Logger.info("Calling select tool from outside")
        if value != '':
            self.selected_tool = value
        else:
            return self.selected_tool

    @property
    def selected_tool(self):
        Logger.info("Getting selected tool! Caller Function is: " + str(inspect.stack()[1][3]))
        return self._selected_tool

    @selected_tool.setter
    def selected_tool(self, value):
        Logger.info("Setting selected tool to " + str(value) + "! Caller Function is: " + str(inspect.stack()[1][3]))
        self._selected_tool = value
        self.apply_tool_change()

    def apply_tool_change(self):
        #select current tool
        self.pconsole_waiter = Clock.schedule_interval(self.wait_for_pconsole, 0.2)

    def wait_for_pconsole(self, dt):
        if pconsole.change_tool(self.selected_tool):
            Logger.info("Waiter Delivering food")
            self.set_temps()
            return False

        if self.user_back_out:
            Logger.info("Waiter Exiting due to back out")
            return False
    def get_state(self):
        Logger.info("Finding State")
        settings = roboprinter.printer_instance._settings
        profile = settings.global_get(['printerProfiles', 'defaultProfile'])

        if 'extruder' in profile:
            extruder_count = int(profile['extruder']['count'])
        else:
            extruder_count = 1

        model = settings.get(['Model'])

        return {'model': model,
                'extruder': extruder_count}

    def set_temps(self):

        #This will cooldown all extruders.
        state = self.get_state()
        roboprinter.printer_instance._printer.commands('M104 T0 S0')
        if int(state['extruder']) > 1:
            roboprinter.printer_instance._printer.commands('M104 T1 S0')

        #since we already parsed temps out into a dictionary in a previous class we just have to apply the temperature
        if self.selected_tool in self.temps:
            Logger.info("Setting " + str(self.selected_tool) + " to " + str(self.temps[self.selected_tool]))
            roboprinter.printer_instance._printer.set_temperature(self.selected_tool, self.temps[self.selected_tool])

        #if there is a bed temp, select that too
        if 'bed' in self.temps:
            selected_tool = 'bed'
            Logger.info("Setting " + str(selected_tool) + " to " + str(self.temps[selected_tool]))
            roboprinter.printer_instance._printer.set_temperature(selected_tool, self.temps[selected_tool])


    def save_offset(self):
        roboprinter.printer_instance._printer.commands('M500')
        pconsole.query_eeprom()
        offset = pconsole.home_offset['Z']
        return offset
