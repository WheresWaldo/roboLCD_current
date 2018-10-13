# -*- coding: utf-8 -*-
# @Author: Matt Pedler
# @Date:   2017-10-12 10:18:47
# @Last Modified by:   Matt Pedler
# @Last Modified time: 2018-01-28 14:56:47

#kivy
from kivy.properties import StringProperty, NumericProperty
from kivy.logger import Logger
from kivy.clock import Clock

#python
from functools import partial

#Robolcd
from RoboLCD import roboprinter
from RoboLCD.lcd.pconsole import pconsole
from RoboLCD.lcd.printer_jog import printer_jog
from RoboLCD.lcd.wizards.preheat_wizard.preheat_overseer import Preheat_Overseer
from RoboLCD.lcd.common_screens import Image_on_Button_Screen, Picture_Image_on_Button_Screen, Temperature_Wait_Screen, Title_Picture_Image_on_Button_Screen
from RoboLCD.lcd.Language import lang

class Filament_Workflow(object):
    """
    This class will just walk through one instance of changing / loading the filament.
    This class can be called multiple times in a row with different tools and setups
    """
    extrude_event = None
    def __init__(self, ext_name, temp, mode, callback, back_button_screen):
        super(Filament_Workflow, self).__init__()
        self.bb = back_button_screen
        self.name = ext_name + "_" + mode
        #check if the printer is printing
        current_data = roboprinter.printer_instance._printer.get_current_data()
        self.is_printing = current_data['state']['flags']['printing']
        self.is_paused = current_data['state']['flags']['paused']
        self.tmp_event = None
        self.s_event = None
        self.E_Position = None
        self.mode = mode
        self.callback = callback
        self.print_temperature = temp
        self.ext_name = ext_name
        self.extruder_control = Extruder_Control(self.ext_name)

        #if it's printing or paused get the position then go to appropriate point in wizard
        if self.is_printing or self.is_paused:

            #get the E position of the selected toolhead
            self.extruder_control.record_E_position()

            #go to extrude or retract page
            if self.mode == 'CHANGE':
                self.retract_screen()

            elif self.mode == 'LOAD':
                self.pull_filament_screen()

        #If it's not printing or paused do the normal flow
        else:
            #set tool temp, then show wait screen
            self.extruder_control.set_temp(self.print_temperature)
            self.preheat_screen()

    def cleanup(self):
        Logger.info("Deleting Filament Workflow")
        #self.temp_screen.cleanup()
        del_list = []
        for self_var in self.__dict__:
            del_list.append(self_var)
        for self_var in del_list:
            #Logger.info("Deleting " + str(self_var))
            del self.__dict__[self_var]
        del self

    def preheat_screen(self, *args):
        """
        the Heating Screen:
            Sets the temperature of the extruder to 230
            Display heating status to user
            Open third screen when temperature hits 230
        """
        #display heating status to user

        #end the event before starting it again
        if self.extrude_event != None:
            self.end_extrude_event()


        if self.mode == 'CHANGE':
            _title = roboprinter.lang.pack['Filament_Wizard']['Title_15']
        else:
            _title = roboprinter.lang.pack['Filament_Wizard']['Title_14']

        self.temp_screen = Temperature_Wait_Screen(self.destination_selector, tool_select=self.ext_name )
        self.temp_screen.change_screen_actions = self.change_screen_event_override
        self.temp_screen.update = self.wait_screen_skip_action
        back_destination = 'preheat_wizard'
        self.bb.make_screen(self.temp_screen,
                         _title,
                         option_function='no_option')

    def wait_screen_skip_action(self):
        Logger.info("Prepare Printer back action!")
        self.bb.back_function_flow()

    def change_screen_event_override(self):
        #set the E position back to it's original position
        if self.E_Position != None:
            Logger.info("Restoring E Position!")
            self.extruder_control.restore_E_Position()

        #if it is printing or paused don't cool down
        if not self.is_printing and not self.is_paused:
            #cooldown
            Logger.info("Cooling Down!")
            self.extruder_control.turn_off_heaters()


    def destination_selector(self):
        if self.mode == "CHANGE":
            self.retract_screen()
        else:
            self.pull_filament_screen()

    def retract_screen(self):
        """
        Pull filament Screen:
            Display instructions to user -- Pull out filament
            Display button that will open fourth screen
        """
        layout = Picture_Image_on_Button_Screen(lang.pack['Filament_Wizard']['Remove_Filament'],
                                           'Icons/Manual_Control/retract_icon.png',
                                           self.pull_filament_screen,
                                           'Icons/Manual_Control/next_button_icon.png',
                                           button_text=lang.pack['Filament_Wizard']['Next'])

        self.bb.make_screen(layout,
                         roboprinter.lang.pack['Filament_Wizard']['Title_25'],
                         option_function='no_option')

        #end the event before starting it again
        if self.extrude_event != None:
            self.end_extrude_event()

        #extrude a little bit before retracting
        self.extruder_control.extrude(20.0)
        self.extrude_event = Clock.schedule_interval(self.retract, 1)

    def pull_filament_screen(self, *args):
        """
        Load filament screen:
            Display instructions to user -- Load filament
            Display button that will open fifth screen
        """

        if self.mode == 'CHANGE':
            _title = roboprinter.lang.pack['Filament_Wizard']['Title_35']
            back_dest = self.name+'[2]'
        else:
            _title = roboprinter.lang.pack['Filament_Wizard']['Title_24']
            back_dest = self.name

        if self.extrude_event != None:
            self.end_extrude_event()

        #body_text,image_source, button_function, button_image, button_text
        layout = Picture_Image_on_Button_Screen(lang.pack['Filament_Wizard']['Cut_Tip'],
                                           'Icons/Manual_Control/cut_filament_icon.png',
                                           self.extrude_screen,
                                           'Icons/Manual_Control/next_button_icon.png',
                                           lang.pack['Filament_Wizard']['Next'])
        self.bb.make_screen(layout,
                         _title,
                         option_function='no_option')

    def extrude_screen(self, *args):
        """
        Final screen / Confirm successful load:
            Extrude filament
            Display instruction to user -- Press okay when you see plastic extruding
            Display button that will move_to_main() AND stop extruding filament
        """
        if self.mode == 'CHANGE':
            _title = roboprinter.lang.pack['Filament_Wizard']['Title_45']
            back_dest = self.name+'[3]'
        else:
            _title = roboprinter.lang.pack['Filament_Wizard']['Title_34']
            back_dest = self.name+'[3]'

        #body_text,image_source, button_function, button_image, button_text
        layout = Picture_Image_on_Button_Screen(lang.pack['Filament_Wizard']['Extrude_Filament'],
                                           'Icons/Manual_Control/extrude_icon.png',
                                           self.end_wizard,
                                           'Icons/Manual_Control/next_button_icon.png',
                                           lang.pack['Filament_Wizard']['Next'],
                                           )
        self.bb.make_screen(layout,
                         _title,
                         option_function='no_option')

        #end the event before starting it again
        Logger.info("Starting the extrude event")
        if self.extrude_event != None:
            self.end_extrude_event()
        self.extrude_event = Clock.schedule_interval(self.extrude, 1)

    def extrude(self, *args):
        #Title_34 and Title 45 are the same thing, but this protects against any different languages besides english in which they may be different.
        if self.bb.title == roboprinter.lang.pack['Filament_Wizard']['Title_45'] or self.bb.title == roboprinter.lang.pack['Filament_Wizard']['Title_34']:

            if self.extruder_control.selected_tool == 'tool0':
                self.extruder_control.extrude(5.0)
            elif self.extruder_control.selected_tool == 'tool1':
                self.extruder_control.move_extruder(25.0, 1500)

        else:
            self.end_extrude_event()
            Logger.info("Canceling due to Screen change")
            self.extrude_event == None
            return False

    def retract(self, *args):
        if self.bb.title == roboprinter.lang.pack['Filament_Wizard']['Title_25']:
            if self.extruder_control.selected_tool == 'tool0':
                self.extruder_control.extrude(-5.0)
            elif self.extruder_control.selected_tool == 'tool1':
                self.extruder_control.move_extruder(-25.0, 1500)
        else:
            self.end_extrude_event()
            Logger.info("Canceling due to Screen change")
            self.extrude_event == None
            return False

    def retract_after_session(self, *args):
        self.extruder_control.extrude(-10.0)

    def end_extrude_event(self, *args):
        self.extrude_event.cancel()

    def end_wizard(self, *args):
        #cancel all extruder events
        self.extrude_event.cancel()

        #set the E position back to it's original position
        if self.extruder_control.E_Position != None:
            self.extruder_control.restore_E_Position()

        #if it is printing or paused don't cool down
        if not self.is_printing and not self.is_paused:
            #retract 10mm
            self.retract_after_session()

            #cooldown
            self.extruder_control.turn_off_heaters()

        #call the callback to the parent workflow
        self.callback()

#This is a small class that will be an interface for moving filament through the extruder and switching extruder controls.
class Extruder_Control(object):
    """docstring for Tool_Mover"""
    E_Position = None #position saver for the Extruder E Position
    def __init__(self, selected_tool = 'tool0'):
        super(Extruder_Control, self).__init__()
        self.controls = roboprinter.printer_instance._printer
        self.change_tool(selected_tool)


    def change_tool(self, tool):
        #wait until tool change has happened
        while not pconsole.change_tool(tool):
            pass

        self.selected_tool = tool

    def temperature(self):
        temps = self.controls.get_current_temperatures()
        current_temperature = int(temps[self.selected_tool]['actual'])

        return current_temperature

    def _move(self, axis, amnt):
        if axis != 'e':
            jogger = {axis:amnt}
            printer_jog.jog(desired=jogger, speed=1500, relative=True)
        else:
            jogger = {axis:amnt}
            printer_jog.jog(desired=jogger, speed=100, relative=True)

    #move extruder
    def move_extruder(self, amount, speed):
        jogger = {'e': amount}
        printer_jog.jog(desired = jogger, speed = speed, relative=True)

    def extrude(self, amount):
        self.controls.extrude(amount)

    def turn_off_heaters(self):
        self.controls.commands('M104 S0')
        self.controls.commands('M140 S0')

    def set_temp(self, temp):
        self.controls.set_temperature(self.selected_tool, temp)

    def record_E_position(self):
        #get the E Position
        #This sends an M114 command to the printer which will return the position for the currently selected toolhead
        pos = pconsole.get_position()
        while not pos:
            pos = pconsole.get_position()

        self.E_Position = pos[3]
        Logger.info("E POS recorded at: " + str(self.E_Position))

    def restore_E_Position(self):
        self.controls.commands("G92 E" + str(self.E_Position))
        Logger.info("E POS set back to " + str(self.E_Position))
