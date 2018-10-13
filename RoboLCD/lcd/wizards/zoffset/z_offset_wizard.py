# -*- coding: utf-8 -*-
# @Author: Matt Pedler
# @Date:   2017-10-11 14:54:41
# @Last Modified by:   Matt Pedler
# @Last Modified time: 2018-02-22 11:48:13
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
from RoboLCD.lcd.pconsole import pconsole
from RoboLCD.lcd.common_screens import Picture_Button_Screen, Wait_Screen, Override_Layout,Picture_Button_Screen_Body, Button_Screen, Extruder_Selector
from RoboLCD.lcd.Language import lang
from RoboLCD.lcd.wizards.wizard_bb import Wizard_BB
from RoboLCD.lcd.wizards.zoffset.z_offset_workflow import Z_Offset_Workflow

#Python
#import gc


'''
This file sets up the Z-Offset Wizard, shows the home screen and extruder select screen, then Links to the
Z offset Workflow. Then finishes with the Finish Wizard screen. This workflow is responsible for setup and
tear down of the Z-Offset wizard.
'''
class ZoffsetWizard(object):
    def __init__(self, state, **kwargs):
        super(ZoffsetWizard, self).__init__()

        self.debug_mode = True

        #set up wizard flow
        self.state = state
        #self.process_state()

        #set up the wizard screen
        self.bb = Wizard_BB()
        self.group = 'Z_Offset_Group'
        #add bb
        roboprinter.robosm.add_widget(self.bb)
        roboprinter.robosm.current = self.bb.name

        self.welcome = None
        self.workflow = None
        self.finish_screen = None


        #initialize wizard variables
        self.z_offset = {}
        self.selected_tool = 'tool0'
        self.dual = False

        #variables for saving old z_offset
        self.old_z_offset = {}
        self.welcome_screen()

    def cleanup(self):
        Logger.info("Deleting: z_offset_wizard")
        roboprinter.robosm.remove_widget(self.bb)
        self.bb.delete_node()

        if self.welcome != None:
            self.welcome.cleanup()
        if self.workflow != None:
            self.workflow.cleanup()
        if self.finish_screen != None:
            self.finish_screen.cleanup()
        del_list = []
        for self_var in self.__dict__:
            del_list.append(self_var)
            self.__dict__[self_var] = ''
        for self_var in del_list:
            #Logger.info("Deleting: " + str(self_var))
            del self.__dict__[self_var]
        #Tell Self to print out any remaining referrers 
        # Logger.info("---> Printing referrers of Z-Offset")
        # gc.collect()
        # for referer in gc.get_referrers(self):
        #     Logger.info(referer)
        # Logger.info("---> Done printing referrers of Z-Offset")
        del self

    def welcome_screen(self):
        #Make screen content
        self.welcome = Button_Screen(lang.pack['ZOffset_Wizard']['Wizard_Description'],
                          self.process_state,
                          button_text=lang.pack['ZOffset_Wizard']['Start'])
        self.welcome.change_screen_actions = self.cleanup
        #populate screen
        self.bb.make_screen(self.welcome,
                            roboprinter.lang.pack['ZOffset_Wizard']['Welcome'],
                            option_function='no_option')

    def process_state(self):
        ext_number = 1
        if 'extruder' in self.state:
            ext_number = int(self.state['extruder'])

        #decide what the layout should be
        if ext_number > 1:
            # self.select_extruder() Re enable this when the new head comes out
            self.selected_tool = 'tool0'
            self.start_workflow()
        else:
            self.selected_tool = 'tool0'
            self.start_workflow()

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
            self.start_workflow()
        else:
            Logger.info("ERROR Invalid selection")
            raise ValueError(str(extruder) + " Is not a valid selection")



    def start_workflow(self):
        if self.dual:
            #this will go through the workflow for both extruders
            def second_extruder():
                self.workflow = Z_Offset_Workflow('tool1',
                                  self.finish_wizard,
                                  self.update_z_offset,
                                  self.bb,
                                  self.group)
            #callback to second extruder function
            self.workflow = Z_Offset_Workflow('tool0',
                              self.second_extruder,
                              self.update_z_offset,
                              self.bb,
                              self.group)
        else:
            #This will go through the workflow for one extruder.
            self.workflow = Z_Offset_Workflow(self.selected_tool,
                              self.finish_wizard,
                              self.update_z_offset,
                              self.bb,
                              self.group)

    #callback to update the Z_Offset for each extruder. This callback does not save anything, it simply records
    #the z offset to be shown in the finish wizard segment.
    def update_z_offset(self, extruder, z_offset):
        self.z_offset[extruder] = z_offset


    def finish_wizard(self, *args, **kwargs):
        title = roboprinter.lang.pack['ZOffset_Wizard']['Z_44']

        #title_text, body_text,image_source, button_function, button_text = roboprinter.lang.pack['Button_Screen']['Default_Button']
        self.finish_screen = Picture_Button_Screen('[size=40][color=#69B3E7]' + lang.pack['ZOffset_Wizard']['Finish_Title'] + '[/color][/size]',
                                       '[size=30]' + lang.pack['ZOffset_Wizard']['Finish_Body1'] + ' {} '.format(self.z_offset['tool0']) + lang.pack['ZOffset_Wizard']['Finish_Body2'],
                                       'Icons/Manual_Control/check_icon.png',
                                       self.end_wizard,
                                       button_text="[size=30]" + lang.pack['ZOffset_Wizard']['Save']
                                        )
        self.finish_screen.change_screen_actions = self.reset_to_zero_on_back
        self.finish_screen.update = self.skip_screen

        self.bb.make_screen(self.finish_screen,
                            title,
                            option_function='no_option')

    def reset_to_zero_on_back(self):
        #set the ZOffset to zero
        Logger.info("Setting the Z-Offset to 0 due to a back screen!")
        roboprinter.printer_instance._printer.commands('M206 Z0.00')
        roboprinter.printer_instance._printer.commands("M851 Z0.00")
        roboprinter.printer_instance._printer.commands("M500")
        roboprinter.printer_instance._printer.commands('M114')

    def skip_screen(self):
        self.bb.back_function_flow()

    def end_wizard(self):
        #home and go back
        roboprinter.printer_instance._printer.commands('G28')
        self.cleanup()
        roboprinter.robosm.go_back_to_main('printer_status_tab')
