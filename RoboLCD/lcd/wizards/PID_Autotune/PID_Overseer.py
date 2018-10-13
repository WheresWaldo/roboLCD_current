# -*- coding: utf-8 -*-
# @Author: Matt Pedler
# @Date:   2017-11-20 12:44:38
# @Last Modified by:   Matt Pedler
# @Last Modified time: 2018-01-28 14:54:53

#kivy
from kivy.logger import Logger

#RoboLCD
from RoboLCD import roboprinter
from RoboLCD.lcd.wizards.wizard_bb import Wizard_BB, Screen_Node
from RoboLCD.lcd.pconsole import pconsole
from RoboLCD.lcd.wizards.preheat_wizard.preheat_overseer import Preheat_Overseer
from RoboLCD.lcd.common_screens import Object_Modal_Question, Object_Button_Screen, Modal_Question_No_Title, Button_Screen, Image_on_Button_Screen, Picture_Image_on_Button_Screen, Temperature_Wait_Screen, Title_Picture_Image_on_Button_Screen, Heater_Selector
from RoboLCD.lcd.Language import lang
from PID_Screens import PID_Test_Screen, PID_Finish_Object
from RoboLCD.lcd.connection_popup import Info_Popup

#Python
import gc

class PID_Overseer(object):
    """docstring for PID_Overseer"""
    def __init__(self, name, title, back_destination):
        super(PID_Overseer, self).__init__()
        self.autotune_complete = False
        pconsole.query_eeprom()
        self.bb = Wizard_BB()
        self.group = 'pid_wizard_group'
        self.welcome = None
        self.pid_screen = None
        self.debug_mode = False

        self.name = name #name of initial screen
        self.title = title
        self.back_destination = back_destination
        self.bb.back_destination = self.back_destination
        self.selected_tool = 'tool0'

        #add bb
        roboprinter.robosm.add_widget(self.bb)
        roboprinter.robosm.current = self.bb.name
        #start wizard
        self.welcome_page()

    def cleanup(self):
        Logger.info("Deleting: PID_Overseer")
        #cleaning up bb elements
        self.bb.delete_node()
        self.bb = ''

        #cleanup workflow
        if self.welcome != None:
            self.welcome.cleanup()
        if self.pid_screen != None:
            self.pid_screen.cleanup()

        #dereference certain functions
        self.back_function_interrupt = ''

        #dereference self    
        del_list = []
        for self_var in self.__dict__:
            del_list.append(self_var)
            self.__dict__[self_var] = '' #set variables to nothing.
        for self_var in del_list:
            #Logger.info("Deleting " + str(self_var))
            del self.__dict__[self_var]

        #Tell Self to print out any remaining referrers 
        # Logger.info("---> Printing referrers of PID_Overseer")
        # gc.collect()
        # for referer in gc.get_referrers(self):
        #     Logger.info(referer)
        # Logger.info("---> Done printing referrers of PID_Overseer")

        del self

    def welcome_page(self):

        self.welcome = Button_Screen(lang.pack['PID_Tool']['Welcome_Screen']['Body'], self.select_extruder,
                               button_text=lang.pack['PID_Tool']['Welcome_Screen']['Button_Text'])

        title = lang.pack['PID_Tool']['Welcome_Screen']['Title']
        self.welcome.change_screen_actions = self.cleanup

        self.bb.make_screen(self.welcome,
                            title,
                            option_function='no_option')

    def select_extruder(self):
        #detirmine machine state and behaviour of the wizard
        model = roboprinter.printer_instance._settings.get(['Model'])

        if model == "Robo R2":
            es = Heater_Selector(self.heater_select, make_screen=self.bb.make_screen, group=self.group)
            es.show_screen()
        else:
            self.heater_select('EXT1')

    def heater_select(self, heater):
        heaters = ['EXT1', 'EXT2', 'BED']

        if heater in heaters:
            tool_dict = {

                'EXT1': '0',
                'EXT2': '1',
                'BED' : '-1'
            }
            self.selected_tool = tool_dict[heater]
            self.start_workflow()
        else:
            Logger.info("ERROR Invalid selection")
            raise ValueError(str(extruder) + " Is not a valid selection")

    def start_workflow(self):
        self.autotune_complete = False #reset autotune
        if self.pid_screen == None:
            self.pid_screen = PID_Test_Screen(self.selected_tool, self.finish_wizard, self.failure_callback, debug=self.debug_mode)
        else:
            self.pid_screen.cleanup()
            self.pid_screen = PID_Test_Screen(self.selected_tool, self.finish_wizard, self.failure_callback, debug=self.debug_mode)

        title = lang.pack['PID_Tool']['Workflow']['Title']

        self.bb.make_screen(self.pid_screen,
                            title,
                            back_function=self.back_function_interrupt,
                            option_function = 'no_option'
                            )

        #parse the correct command
        #The stage 3 variable will detirmine how many cycles the PID tool will do. This is so our Testers can easily adjust this number without having to consult me.
        if not self.debug_mode:
            command = 'M303 C' + str(lang.pack['PID_Tool']['Workflow']['Stage3']) + ' E' + self.selected_tool
        else:
            def deffered_action(*args, **kwargs):
                command = ""

        if not self.debug_mode:
            #if it's the bed then set temp to 100, else set temp to 240
            if int(self.selected_tool) < 0:
                command = command + " S" + lang.pack['PID_Tool']['Workflow']['Target_Bed']
            else:
                command = command + " S" + lang.pack['PID_Tool']['Workflow']['Target_Ext']
        else:
            #Just make the wizard dwell for a little back_function_interrupt
            command = "G4 S3"

        Logger.info("Command sent is: " + str(command))

        #start the test
        roboprinter.printer_instance._printer.commands(command)
        roboprinter.printer_instance._printer.commands("M118 ACTION COMPLETE!")

    def back_function_interrupt(self):
        if self.autotune_complete:
            self.bb.back_function_flow()
        else:
            Info_Popup(lang.pack['PID_Tool']['Prevent_Back_Screen']['Title'], lang.pack['PID_Tool']['Prevent_Back_Screen']['Body']).show()

    def failure_callback(self):
        self.autotune_complete = True
        def cancel():
            roboprinter.robosm.go_back_to_main('printer_status_tab')

        layout = Button_Screen(lang.pack['PID_Tool']['Failure_Screen']['Body'],
                                cancel )

        title = lang.pack['PID_Tool']['Failure_Screen']['Title']
        self.bb.make_screen(layout, title, option_function='no_option')


    def finish_wizard(self, final_PID):
        self.autotune_complete = True
        
        def save_pid():
            self.save_PID(final_PID)
            

        body = lang.pack['PID_Tool']['Finish_Wizard']['Body']
        new_pid = lang.pack['PID_Tool']['Finish_Wizard']['New_PID']


        #make the text_object to put into the modal question
        finish_object = PID_Finish_Object(body, new_pid, final_PID)


        layout = Object_Modal_Question(
                                finish_object,
                                lang.pack['PID_Tool']['Finish_Wizard']['Save'],
                                lang.pack['PID_Tool']['Finish_Wizard']['Cancel'],
                                save_pid,
                                self.goto_main)
        title = lang.pack['PID_Tool']['Finish_Wizard']['Title']

        self.bb.make_screen(layout,
                            title,
                            option_function='no_option')

    def save_PID(self, PID):
        #construct PID save command
        pid_command = ''
        if self.selected_tool == "-1":
            pid_command = 'M304 P' + str(PID['P']) + " I" + str(PID['I']) + " D" + str(PID['D'])
        else:
            pid_command = 'M301 P' + str(PID['P']) + " I" + str(PID['I']) + " D" + str(PID['D'])

        #save PID
        roboprinter.printer_instance._printer.commands(pid_command)
        roboprinter.printer_instance._printer.commands("M500") #save

        #create a button screen
        layout = Button_Screen(lang.pack['PID_Tool']['Save_Screen']['Body'] ,
                               self.goto_main )

        title = lang.pack['PID_Tool']['Save_Screen']['Title']
        self.bb.make_screen(layout, 
                            title, 
                            option_function='no_option')

    def goto_main(self):
        #cleanup the wizard
        self.cleanup()
        roboprinter.robosm.go_back_to_main('printer_status_tab')
