# -*- coding: utf-8 -*-
# @Author: Matt Pedler
# @Date:   2017-09-28 12:22:30
# @Last Modified by:   Matt Pedler
# @Last Modified time: 2018-01-28 14:55:31
#kivy
from kivy.logger import Logger
from kivy.properties import ObjectProperty, StringProperty, BooleanProperty, NumericProperty, ListProperty
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout

#python
import gc

#RoboLCD
from RoboLCD.lcd.wizards.wizard_bb import Wizard_BB, Screen_Node
from RoboLCD import roboprinter
from RoboLCD.lcd.printer_jog import printer_jog
from RoboLCD.lcd.common_screens import Button_Group_Observer, OL_Button, Quad_Icon_Layout, Button_Screen, Picture_Button_Screen, Modal_Question, Wait_Screen, Point_Layout
from RoboLCD.lcd.pconsole import pconsole
from RoboLCD.lcd.connection_popup import Error_Popup, Warning_Popup
from RoboLCD.lcd.wizards.bed_calibration.bedcal_workflow import BedCal_Workflow

#Python
from functools import partial

class Bed_Calibration(object):
    """Bed_Calibration Allows the user to move the head to three different points to manually level the bed through the
       Screws on the bed"""
    def __init__(self, name, title, back_destination):
        super(Bed_Calibration, self).__init__()

        #setup the wizard_bb screen
        self.bb = Wizard_BB()
        self.group = 'pid_wizard_group'
        self.workflow = None
        self.finish_wizard = None
        self.welcome = None
        self.debug = False

        self.name = name #name of initial screen
        self.title = title
        self.back_destination = back_destination
        self.bb.back_destination = self.back_destination
        self.selected_tool = 'tool0'

        #add bb
        roboprinter.robosm.add_widget(self.bb)
        roboprinter.robosm.current = self.bb.name

        # Check the debug state. If true, print out a list of instances of
        # Bed_Calibration recognized by the garbage collector
        if self.debug:
            Logger.info("---> Checking Bed_Calibration instances")
            obj_len = 0
            for obj in gc.get_objects():
                if isinstance(obj, Bed_Calibration):
                    obj_len += 1
                    Logger.info("GC: " + str(obj))
            Logger.info("There are " + str(obj_len) + " Bed_Calibration Objects active")

            # Print out the instance of this class. The name of the instance and
            # address in memory will be printed.
            Logger.info("SELF: " + str(self))

        #pconsole.query_eeprom()
        self.model = roboprinter.printer_instance._settings.get(['Model'])
        self.welcome_screen()
        self.mode = "manual"

    def cleanup(self):
        Logger.info("Cleaning up the bed Calibration Wizard!")
        self.bb.delete_node()

        #cleanup workflows
        if self.welcome != None:
            self.welcome.cleanup()
            
        if self.workflow != None:
            self.workflow.cleanup()

        if self.finish_wizard != None:
            self.finish_wizard.cleanup()

        #dereference self    
        del_list = []
        for self_var in self.__dict__:
            del_list.append(self_var)
            self.__dict__[self_var] = '' #set variables to nothing.
        for self_var in del_list:
            #Logger.info("Deleting " + str(self_var))
            del self.__dict__[self_var]

        #Tell Self to print out any remaining referrers 
        # Logger.info("---> Printing referrers of Bed_Calibration")
        # gc.collect()
        # for referer in gc.get_referrers(self):
        #     Logger.info(referer)
        # Logger.info("---> Done printing referrers of Bed_Calibration")
        del self

    def welcome_screen(self):
        self.welcome = Button_Screen(roboprinter.lang.pack['Bed_Cal_Wizard']['Welcome']['Body'],
                               self.tighten_all_screw_instructions,
                               button_text = roboprinter.lang.pack['Bed_Cal_Wizard']['Welcome']['Button'])
        title = roboprinter.lang.pack['Bed_Cal_Wizard']['Welcome']['Title']
        name = 'welcome_bed_calibration'
        back_destination = roboprinter.robo_screen()
        self.welcome.change_screen_actions = self.cleanup
        self.bb.make_screen(self.welcome,
                            title,
                            option_function='no_option')

    def tighten_all_screw_instructions(self):
        layout = Button_Screen(roboprinter.lang.pack['Bed_Cal_Wizard']['Tilt_Instructions']['Body'],
                               self.check_for_valid_start,
                               button_text = roboprinter.lang.pack['Bed_Cal_Wizard']['Tilt_Instructions']['Button'])
        title = roboprinter.lang.pack['Bed_Cal_Wizard']['Tilt_Instructions']['Title']
        name = 'tilt1'
        back_destination = roboprinter.robo_screen()

        self.bb.make_screen(layout,
                            title,
                            option_function='no_option')

    def check_for_valid_start(self):
        start = self.check_offset()

        #if the ZOffset is not right don't allow the user to continue
        if start:
            self.ask_for_mode()
        else:
            zoff = pconsole.home_offset['Z']
            ep = Error_Popup(roboprinter.lang.pack['Warning']['Z_Offset_Warning']['Title'], roboprinter.lang.pack['Warning']['Z_Offset_Warning']['Body1'] + " " +  str(zoff) + " " + roboprinter.lang.pack['Warning']['Z_Offset_Warning']['Body2'],callback=partial(roboprinter.robosm.go_back_to_main, tab='printer_status_tab'))
            ep.open()

    def ask_for_mode(self):

        def manual():
            self.mode = "manual"
            self.start_workflow()
        def guided():
            self.mode = "guided"
            self.start_workflow()

        layout = Modal_Question(roboprinter.lang.pack['Bed_Cal_Wizard']['Mode']['Sub_Title'],
                       roboprinter.lang.pack['Bed_Cal_Wizard']['Mode']['Body'],
                       roboprinter.lang.pack['Bed_Cal_Wizard']['Mode']['Button1'],
                       roboprinter.lang.pack['Bed_Cal_Wizard']['Mode']['Button2'],
                       manual,
                       guided)

        title = roboprinter.lang.pack['Bed_Cal_Wizard']['Mode']['Title']
        name = 'guided_or_manual'
        back_destination = roboprinter.robo_screen()

        self.bb.make_screen(layout,
                            title,
                            option_function='no_option')




    #check the offset to see if it is in an acceptable range
    def check_offset(self):

        offset = float(pconsole.home_offset['Z'])
        #make sure the range is within -20 - 0
        if offset > -20.00 and not offset > 0.00 and offset != 0.00:
            return True
        else:
            return False

    def start_workflow(self):
        self.workflow = BedCal_Workflow(self.mode, self.finish_screws_instructions, self.bb, debug=self.debug)


    def finish_screws_instructions(self):
        layout = Button_Screen(roboprinter.lang.pack['Bed_Cal_Wizard']['Tilt_Instructions']['Body'],
                               self.finish_bed_cal_wizard,
                               button_text = roboprinter.lang.pack['Bed_Cal_Wizard']['Tilt_Instructions']['Button'])
        title = roboprinter.lang.pack['Bed_Cal_Wizard']['Tilt_Instructions']['Title']
        name = 'tilt2'
        back_destination = 'guided_or_manual'

        self.bb.make_screen(layout,
                            title,
                            option_function='no_option')

    def finish_bed_cal_wizard(self):

        self.finish_wizard = Picture_Button_Screen(roboprinter.lang.pack['Bed_Cal_Wizard']['Finish_Wizard']['Sub_Title'],
                                      roboprinter.lang.pack['Bed_Cal_Wizard']['Finish_Wizard']['Body'],
                                      'Icons/Manual_Control/check_icon.png',
                                      self.goto_main)
        title = roboprinter.lang.pack['Bed_Cal_Wizard']['Finish_Wizard']['Title']
        name = 'finish_wizard'
        back_destination = roboprinter.robo_screen()

        self.bb.make_screen(self.finish_wizard,
                            title,
                            option_function='no_option')

    def goto_main(self):
        roboprinter.printer_instance._printer.commands('G28')
        roboprinter.robosm.go_back_to_main('utilities_tab')
        self.cleanup()
        
