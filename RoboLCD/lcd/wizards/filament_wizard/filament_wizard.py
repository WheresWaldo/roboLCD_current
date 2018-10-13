# -*- coding: utf-8 -*-
# @Author: Matt Pedler
# @Date:   2017-10-09 11:47:59
# @Last Modified by:   Matt Pedler
# @Last Modified time: 2018-01-28 15:21:30

#kivy
from kivy.uix.button import Button
from kivy.properties import StringProperty, NumericProperty
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.uix.togglebutton import ToggleButton
from kivy.logger import Logger
from kivy.clock import Clock

#python
from functools import partial
import copy
import gc

#Robolcd
from RoboLCD import roboprinter
from RoboLCD.lcd.pconsole import pconsole
from RoboLCD.lcd.wizards.preheat_wizard.preheat_overseer import Preheat_Overseer
from RoboLCD.lcd.common_screens import Image_on_Button_Screen, Picture_Image_on_Button_Screen, Temperature_Wait_Screen, Title_Picture_Image_on_Button_Screen, Extruder_Selector, Wizard_Screen_Controls
from RoboLCD.lcd.Language import lang
from filament_workflow import Filament_Workflow
from RoboLCD.lcd.wizards.wizard_bb import Wizard_BB, Screen_Node

class FilamentWizard(object):

    extrude_event = None
    def __init__(self, loader_changer, name, title, back_destination, state,  **kwargs):
        super(FilamentWizard, self).__init__(**kwargs)
        self.bb = Wizard_BB()
        self.group = 'filament_wizard_group'
        self.welcome = None
        self.ph_overseer = None
        self.workflow = None
        self.debug_mode = True

        self.name = name #name of initial screen
        self.title = title
        self.back_destination = back_destination
        self.bb.back_destination = self.back_destination
        self.load_or_change = loader_changer
        self.dual = False
        self.state = state
        self.selected_tool = 'tool0'
        current_data = roboprinter.printer_instance._printer.get_current_data()
        self.is_printing = current_data['state']['flags']['printing']
        self.is_paused = current_data['state']['flags']['paused']

        #add bb
        roboprinter.robosm.add_widget(self.bb)
        roboprinter.robosm.current = self.bb.name

        # Check debug state, if true, print out instances of FilamentWizard
        #  recognized by the garbage collector
        # if self.debug_mode:
        #     Logger.info("--->Checking FilamentWizard")
        #     obj_len = 0
        #     for obj in gc.get_objects():
        #         if isinstance(obj, FilamentWizard):
        #             obj_len += 1
        #             Logger.info("GC: " + str(obj))
        #     Logger.info("There are " + str(obj_len) + " FilamentWizard Objects active")

        #     # Print out the instance of this class. The name of the instance and
        #     # address in memory will be printed
        #     Logger.info("SELF: " + str(self))

        #go to first screen
        self.first_screen()

    def cleanup(self):
        Logger.info("Deleting: filament_wizard")
        #Clean up the wizard
        roboprinter.robosm.remove_widget(self.bb)
        self.bb.delete_node()

        if self.welcome != None:
            self.welcome.cleanup()
        if self.ph_overseer != None:
            self.ph_overseer.cleanup()
        if self.workflow != None:
            self.workflow.cleanup()
        del_list = []
        for self_var in self.__dict__:
            del_list.append(self_var)
        for self_var in del_list:
            #Logger.info("Deleting " + str(self_var))
            del self.__dict__[self_var]

        #Tell Self to print out any remaining referrers 
        # Logger.info("---> Printing referrers of FilamentWizard")
        # gc.collect()
        # for referer in gc.get_referrers(self):
        #     Logger.info(referer)
        # Logger.info("---> Done printing referrers of FilamentWizard")
        del self

    def process_machine_state(self):
        ext_number = 1
        if 'extruder' in self.state:
            ext_number = int(self.state['extruder'])

        #decide what the layout should be
        if ext_number > 1:
            self.select_extruder()
        else:
            self.choose_material()


    def first_screen(self):
        """
        First Screen:
            displays Start button that will open second_screen
        """
        self.welcome = Picture_Image_on_Button_Screen(lang.pack['Filament_Wizard']['Wizard_Description'],
                                                'Icons/Manual_Control/info_icon.png',
                                                self.process_machine_state,
                                                'Icons/Manual_Control/start_button_icon.png',
                                                lang.pack['Filament_Wizard']['Start'])
        self.welcome.change_screen_actions = self.cleanup
        self.bb.make_screen(self.welcome,
                         self.title,
                         option_function='no_option')

    def choose_material(self, *args):
        #if we are printing we want to change the material at the current temperature
        if self.is_printing or self.is_paused:
            temps  = roboprinter.printer_instance._printer.get_current_temperatures()
            current_temperature = [0,0]
            extruder = self.selected_tool

            if extruder in temps and 'actual' in temps[extruder] and 'target' in temps[extruder]:
                current_temperature = [int(temps[extruder]['actual']), int(temps[extruder]['target'])]

            self.collect_heat_settings(current_temperature[1], 0)
        else:
            Logger.info("Making Preheat_Overseer with group: " + str(self.group))
            ### FLAGGED FOR CLEAN UP
            # self.ph_overseer = Preheat_Overseer(end_point=self.collect_heat_settings,
            self.ph_overseer = Preheat_Overseer(end_point=self.collect_heat_settings,
                             name='preheat_wizard',
                             title=roboprinter.lang.pack['Utilities']['Preheat'],
                             back_destination=self.bb.name,
                             dual = self.dual,
                             back_button_screen = self.bb,
                             group = self.group)


    def select_extruder(self):
        #detirmine machine state and behaviour of the wizard
        es = Extruder_Selector(self.dual_or_single_fork, make_screen=self.bb.make_screen, group=self.group)
        es.show_screen()

    def dual_or_single_fork(self, extruder):
        extruders = ['EXT1', 'EXT2', 'BOTH']

        if extruder in extruders:
            if extruder == 'BOTH':
                self.dual = True
            else:
                self.dual = False
                tool_dict = {
                    'EXT1': 'tool0',
                    'EXT2': 'tool1'
                }
                self.selected_tool = tool_dict[extruder]
            self.choose_material()
        else:
            Logger.info("ERROR Invalid selection")
            raise ValueError(str(extruder) + " Is not a valid selection")

    def collect_heat_settings(self, extruder, bed):
        if self.dual:
            def second_extruder():
                self.print_temperature = extruder[1]
                self.workflow = Filament_Workflow('tool1', self.print_temperature, self.load_or_change, self.finish_wizard, self.bb)

            #
            self.print_temperature = extruder[0]
            self.workflow = Filament_Workflow('tool0', self.print_temperature, self.load_or_change, second_extruder, self.bb)


        else:
            self.print_temperature = extruder
            self.workflow = Filament_Workflow(self.selected_tool, self.print_temperature, self.load_or_change, self.finish_wizard,self.bb)


    def finish_wizard(self):
        #title_text, body_text,image_source, button_function, button_image, button_text
        layout = Title_Picture_Image_on_Button_Screen(lang.pack['Filament_Wizard']['Complete_Title'],
                                                 lang.pack['Filament_Wizard']['Complete_Body'],
                                                 'Icons/Manual_Control/check_icon.png',
                                                 self.goto_main,
                                                 'Icons/Manual_Control/ok_button_icon.png',
                                                 lang.pack['Filament_Wizard']["Ok"])

        if self.load_or_change == 'CHANGE':
            _title = roboprinter.lang.pack['Filament_Wizard']['Title_55']

        else:
            _title = roboprinter.lang.pack['Filament_Wizard']['Title_44']

        back_destination = roboprinter.robo_screen()
        self.bb.make_screen(layout,
                         _title,
                         option_function='no_option')

    def goto_main(self):
        Logger.info("Going to main " + str(self))
        self.cleanup()
        roboprinter.robosm.go_back_to_main()
