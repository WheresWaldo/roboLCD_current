# -*- coding: utf-8 -*-
# @Author: Matt Pedler
# @Date:   2017-12-07 16:45:38
# @Last Modified by:   Matt Pedler
# @Last Modified time: 2018-01-28 14:55:59
from kivy.logger import Logger
from kivy.properties import ObjectProperty, StringProperty, BooleanProperty, NumericProperty, ListProperty
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout

#RoboLCD
from RoboLCD import roboprinter
from RoboLCD.lcd.printer_jog import printer_jog
from RoboLCD.lcd.common_screens import Button_Group_Observer, OL_Button, Quad_Icon_Layout, Button_Screen, Picture_Button_Screen, Modal_Question, Wait_Screen, Point_Layout
from RoboLCD.lcd.pconsole import pconsole
from RoboLCD.lcd.connection_popup import Error_Popup, Warning_Popup
from RoboLCD.lcd.wizards.bed_calibration.bedcal_screens import Quad_Icon_Layout

#Python
from functools import partial
import gc


class BedCal_Workflow(object):
    """docstring for BedCal_Workflow"""
    def __init__(self, mode, end_point, back_button, debug=False):
        super(BedCal_Workflow, self).__init__()
        self.mode = mode
        self.end_point = end_point
        self.bb = back_button
        self.overall_counter = 0
        self.wait_screen = None
        self.debug = debug

        self.prepare_printer()
        # Check the debug state. If true, print out a list of instances of
        # BedCal_Workflow recognized by the garbage collector
        # if self.debug:
        #     Logger.info("---> Checking BedCal_Workflow instances")
        #     obj_len = 0
        #     for obj in gc.get_objects():
        #         if isinstance(obj, BedCal_Workflow):
        #             obj_len += 1
        #             Logger.info("GC: " + str(obj))
        #     Logger.info("There are " + str(obj_len) + " BedCal_Workflow Objects active")

        #     # Print out the instance of this class. The name of the instance and
        #     # address in memory will be printed.
        #     Logger.info("SELF: " + str(self))


    def cleanup(self):
        Logger.info("Cleaning Up Bed Cal Workflow")

        self.bb = ''

        #clean wait screen
        if self.wait_screen != None:
            self.wait_screen.update = '' #dereference update
            self.wait_screen.cleanup()

        #dereference self    
        del_list = []
        for self_var in self.__dict__:
            del_list.append(self_var)
            self.__dict__[self_var] = '' #set variables to nothing.
        for self_var in del_list:
            #Logger.info("Deleting " + str(self_var))
            del self.__dict__[self_var]

        #Tell Self to print out any remaining referrers 
        # Logger.info("---> Printing referrers of BedCal_Workflow")
        # gc.collect()
        # for referer in gc.get_referrers(self):
        #     Logger.info(referer)
        # Logger.info("---> Done printing referrers of BedCal_Workflow")
        del self
        
    def prepare_printer(self):
            #kill heaters
            roboprinter.printer_instance._printer.commands('M104 S0')
            roboprinter.printer_instance._printer.commands('M140 S0')
            roboprinter.printer_instance._printer.commands('M106 S255')
    
            roboprinter.printer_instance._printer.commands('G28') #Home Printer
            roboprinter.printer_instance._printer.commands('G1 X5 Y10 F5000') # go to first corner
            roboprinter.printer_instance._printer.commands('G1 Z5')
            roboprinter.printer_instance._printer.commands('M114')
            roboprinter.printer_instance._printer.commands('M118 ACTION COMPLETE!')
    
            fork_mode = self.open_3_point_screen
            title = roboprinter.lang.pack['Bed_Cal_Wizard']['Prepare']['Title1']
            if self.mode == "guided":
                fork_mode = self.guided_instructions
                title = roboprinter.lang.pack['Bed_Cal_Wizard']['Prepare']['Title2']
                
    
            self.wait_screen = Wait_Screen(fork_mode,
                                 roboprinter.lang.pack['Bed_Cal_Wizard']['Prepare']['Sub_Title'],
                                 roboprinter.lang.pack['Bed_Cal_Wizard']['Prepare']['Body'],
                                 watch_action=True)
            self.wait_screen.update = self.wait_screen_skip_action
    
    
            self.bb.make_screen(self.wait_screen,
                            title,
                            option_function='no_option')

    def wait_screen_skip_action(self):
        Logger.info("Prepare Printer back action!")
        self.bb.back_function_flow()
    
    def guided_instructions(self, *args, **kwargs):
        #turn off fans
        roboprinter.printer_instance._printer.commands('M106 S0')
        point_string = roboprinter.lang.pack['Bed_Cal_Wizard']['Guided_Instructions']['Error']
        screw = roboprinter.lang.pack['Bed_Cal_Wizard']['Guided_Instructions']['Error']
        point_icon = "Icons/Bed_Calibration/Bed placement left.png"
        body = (roboprinter.lang.pack['Bed_Cal_Wizard']['Guided_Instructions']['Body1'] + screw + roboprinter.lang.pack['Bed_Cal_Wizard']['Guided_Instructions']['Body2'])
        self.counter = 1
        self.done = False
        def point_1():
            point_string = roboprinter.lang.pack['Bed_Cal_Wizard']['Guided_Instructions']['L_Point']
            screw = roboprinter.lang.pack['Bed_Cal_Wizard']['Guided_Instructions']['LF_Screw']
            point_icon = "Icons/Bed_Calibration/Bed placement left.png"
            self.update_body(point_string, screw, point_icon)

            roboprinter.printer_instance._printer.commands('G1 Z10')
            roboprinter.printer_instance._printer.commands('G1 X35 Y35 F5000') # go to first corner
            roboprinter.printer_instance._printer.commands('G1 Z0')

        def point_2():
            point_string = roboprinter.lang.pack['Bed_Cal_Wizard']['Guided_Instructions']['R_Point']
            screw = roboprinter.lang.pack['Bed_Cal_Wizard']['Guided_Instructions']['RF_Screw']
            point_icon = "Icons/Bed_Calibration/Bed placement right.png"
            self.update_body(point_string, screw, point_icon)
            
            roboprinter.printer_instance._printer.commands('G1 Z10')
            roboprinter.printer_instance._printer.commands('G1 X160 Y35 F5000') # go to first corner
            roboprinter.printer_instance._printer.commands('G1 Z0')

        def point_3():
            point_string = roboprinter.lang.pack['Bed_Cal_Wizard']['Guided_Instructions']['BR_Point']
            screw = roboprinter.lang.pack['Bed_Cal_Wizard']['Guided_Instructions']['BR_Screw']
            point_icon = "Icons/Bed_Calibration/Bed placement back right.png"
            self.update_body(point_string, screw, point_icon)
            
            roboprinter.printer_instance._printer.commands('G1 Z10')
            roboprinter.printer_instance._printer.commands('G1 X160 Y160 F5000') # go to first corner
            roboprinter.printer_instance._printer.commands('G1 Z0')

        def point_4():
            point_string = roboprinter.lang.pack['Bed_Cal_Wizard']['Guided_Instructions']['BL_Point']
            screw = roboprinter.lang.pack['Bed_Cal_Wizard']['Guided_Instructions']['BL_Screw']
            point_icon = "Icons/Bed_Calibration/Bed placement back left.png"
            self.update_body(point_string, screw, point_icon)
            
            roboprinter.printer_instance._printer.commands('G1 Z10')
            roboprinter.printer_instance._printer.commands('G1 X35 Y160 F5000') # go to first corner
            roboprinter.printer_instance._printer.commands('G1 Z0')


        def next_point():
            points = [point_1, point_2, point_3, point_4]

            if self.counter == 4 and not self.done:
                self.counter = 0
                self.done = True
            elif self.counter == 4 and self.done:
                self.end_point()
                return

            points[self.counter]()    

            self.counter += 1   

        self.guided_layout = Picture_Button_Screen(point_string, 
                                       body,
                                       point_icon,
                                       next_point,
                                       button_text = roboprinter.lang.pack['Bed_Cal_Wizard']['Guided_Instructions']['Button_Text2'] + str(self.overall_counter) + roboprinter.lang.pack['Bed_Cal_Wizard']['Guided_Instructions']['Button_Text3'])

        title = roboprinter.lang.pack['Bed_Cal_Wizard']['Guided_Instructions']['Title']
        name = 'adjust_screws'
        back_destination = 'guided_or_manual'

        self.bb.make_screen(self.guided_layout,
                        title,
                        option_function='no_option')

        point_1()

    def update_body(self, point_string, screw, icon):
        self.overall_counter += 1
        body = (roboprinter.lang.pack['Bed_Cal_Wizard']['Guided_Instructions']['Body1'] + screw + roboprinter.lang.pack['Bed_Cal_Wizard']['Guided_Instructions']['Body2'])
        self.guided_layout.body_text = body
        self.guided_layout.title_text = point_string
        self.guided_layout.image_source = icon
        self.guided_layout.button_text = roboprinter.lang.pack['Bed_Cal_Wizard']['Guided_Instructions']['Button_Text2'] + str(self.overall_counter) + roboprinter.lang.pack['Bed_Cal_Wizard']['Guided_Instructions']['Button_Text3']

    def open_3_point_screen(self, *args, **kwargs):
        #turn off fans
        roboprinter.printer_instance._printer.commands('M106 S0')
       
        def point_1(state):
            if state:
                roboprinter.printer_instance._printer.commands('G1 Z10')
                roboprinter.printer_instance._printer.commands('G1 X35 Y35 F5000') # go to first corner
                roboprinter.printer_instance._printer.commands('G1 Z0')

        def point_2(state):
            if state:
                roboprinter.printer_instance._printer.commands('G1 Z10')
                roboprinter.printer_instance._printer.commands('G1 X160 Y35 F5000') # go to first corner
                roboprinter.printer_instance._printer.commands('G1 Z0')

        def point_3(state):
            if state:
                roboprinter.printer_instance._printer.commands('G1 Z10')
                roboprinter.printer_instance._printer.commands('G1 X160 Y160 F5000') # go to first corner
                roboprinter.printer_instance._printer.commands('G1 Z0')

        def point_4(state):
            if state:
                roboprinter.printer_instance._printer.commands('G1 Z10')
                roboprinter.printer_instance._printer.commands('G1 X35 Y160 F5000') # go to first corner
                roboprinter.printer_instance._printer.commands('G1 Z0')

        #make the button observer
        point_observer = Button_Group_Observer()

        #make the buttons
        p1 = OL_Button(roboprinter.lang.pack['Bed_Cal_Wizard']['Manual_Instructions']['Left'], 
                       "Icons/Bed_Calibration/Bed placement left.png",
                       point_1,
                       enabled = True,
                       observer_group = point_observer)
        p2 = OL_Button(roboprinter.lang.pack['Bed_Cal_Wizard']['Manual_Instructions']['Right'], 
                       "Icons/Bed_Calibration/Bed placement right.png",
                       point_2,
                       enabled = False,
                       observer_group = point_observer)
        p3 = OL_Button(roboprinter.lang.pack['Bed_Cal_Wizard']['Manual_Instructions']['Back_Right'], 
                       "Icons/Bed_Calibration/Bed placement back right.png",
                       point_3,
                       enabled = False,
                       observer_group = point_observer)
        p4 = OL_Button(roboprinter.lang.pack['Bed_Cal_Wizard']['Manual_Instructions']['Back_Left'], 
                       "Icons/Bed_Calibration/Bed placement back left.png",
                       point_4,
                       enabled = False,
                       observer_group = point_observer)

        bl2 = [p1, p2]
        bl1 = [p4, p3]

        #make screen
        layout = Quad_Icon_Layout(bl1, bl2,  roboprinter.lang.pack['Bed_Cal_Wizard']['Manual_Instructions']['Sub_Title'])
        back_destination = roboprinter.robo_screen()
        title = roboprinter.lang.pack['Bed_Cal_Wizard']['Manual_Instructions']['Title']

        self.bb.make_screen(layout,
                        title,
                        option_function=self.end_point,
                        option_icon="Icons/Slicer wizard icons/next.png") 