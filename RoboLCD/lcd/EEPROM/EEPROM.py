# -*- coding: utf-8 -*-
# @Author: Matt Pedler
# @Date:   2017-10-19 13:34:53
# @Last Modified by:   Matt Pedler
# @Last Modified time: 2018-01-28 15:08:44
# coding=utf-8

#Kivy
from kivy.logger import Logger
from kivy.uix.button import Button
from kivy.properties import StringProperty, NumericProperty
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.clock import Clock

#RoboLCD
from RoboLCD.lcd.scrollbox import Scroll_Box_Even_Button, Scroll_Box_Even
from RoboLCD.lcd.session_saver import session_saver
from RoboLCD.lcd.pconsole import pconsole
from RoboLCD import roboprinter
from RoboLCD.lcd.connection_popup import Status_Popup
from RoboLCD.lcd.common_screens import Modal_Question_No_Title, Button_Screen
from RoboLCD.lcd.wizards.wizard_bb import Wizard_BB, Screen_Node
from RoboLCD.lcd.file_system.file_screen import Scroll_Box_File_List
from RoboLCD.lcd.EEPROM.EEPROM_screens import Scroll_Box_EEPROM_List, Change_Value


class EEPROM(object):
    #self._generate_backbutton_screen(name=_name, title=kwargs['title'], back_destination=kwargs['back_destination'], content=layout)
    def __init__(self, *args, **kwargs):
        self.buttons = []
        self.name = kwargs['name']
        self.title = kwargs['title']
        self.back_destination = kwargs['back_destination']

        #set up the wizard screen
        self.bb = Wizard_BB()
        self.group = 'EEPROM_Group'
       
        #add bb
        roboprinter.robosm.add_widget(self.bb)
        roboprinter.robosm.current = self.bb.name


        model = roboprinter.printer_instance._settings.get(['Model'])
        self.refresh_eeprom()

        if model == "Robo R2":
            #add bed PID for the R2
            self.button_order = [
                                 roboprinter.lang.pack['EEPROM']['Home_Offset'],
                                 roboprinter.lang.pack['EEPROM']['Probe_Offset'] , 
                                 roboprinter.lang.pack['EEPROM']['Steps_Unit'], 
                                 roboprinter.lang.pack['EEPROM']['Accelerations'], 
                                 roboprinter.lang.pack['EEPROM']['Max_Accelerations'],  
                                 roboprinter.lang.pack['EEPROM']['Filament_Settings'], 
                                 roboprinter.lang.pack['EEPROM']['Feed_Rates'], 
                                 roboprinter.lang.pack['EEPROM']['PID_Settings'],
                                 roboprinter.lang.pack['EEPROM']['Bed_PID'], 
                                 roboprinter.lang.pack['EEPROM']['Advanced'],
                                 roboprinter.lang.pack['EEPROM']['Linear_Advanced'],
                                 roboprinter.lang.pack['EEPROM']['Reset']
                                 ]
        else:
            self.button_order = [
                                 roboprinter.lang.pack['EEPROM']['Home_Offset'],
                                 roboprinter.lang.pack['EEPROM']['Probe_Offset'] , 
                                 roboprinter.lang.pack['EEPROM']['Steps_Unit'], 
                                 roboprinter.lang.pack['EEPROM']['Accelerations'], 
                                 roboprinter.lang.pack['EEPROM']['Max_Accelerations'],  
                                 roboprinter.lang.pack['EEPROM']['Filament_Settings'], 
                                 roboprinter.lang.pack['EEPROM']['Feed_Rates'], 
                                 roboprinter.lang.pack['EEPROM']['PID_Settings'],
                                 roboprinter.lang.pack['EEPROM']['Advanced'],
                                 roboprinter.lang.pack['EEPROM']['Linear_Advanced'],
                                 roboprinter.lang.pack['EEPROM']['Reset']
                                 ]   
        self.load_eeprom()     

    def load_eeprom(self):
        eeprom_list = []
        for entry in self.button_order:
            if entry in self.eeprom_dictionary and self.eeprom_dictionary[entry]['values'] != {}:
                eeprom_list.append(self.eeprom_dictionary[entry])

        #make node
        self.EEPROM_Node = EEPROM_Node(data=eeprom_list, title=self.title)

        #render screen with list
        self.EEPROM_screen = Scroll_Box_EEPROM_List(self.EEPROM_Node.data, self.open_setting)

        self.bb.make_screen(self.EEPROM_screen,
                            title = self.title,
                            back_function = self.previous_list,
                            option_function = 'no_option'
                                )
    
    def refresh_eeprom(self):
        pconsole.query_eeprom()

        '''
        This dictionary contains a few defining elements for each EEPROM entry that we want to display
        name: This is the name that will be displayed on the screen for this value
        command: This is the specific gcode command that this entry is attached to
        filter: This defines what values will be shown to the user
        order: This defines the order that the values will be shown to the user
        range: This will define the numbers by which the user will be able to edit the entry
        values: This will hold the actual values scraped from the EEPROM
        '''
        self.eeprom_dictionary = {
            
            roboprinter.lang.pack['EEPROM']['Home_Offset'] : {'name': roboprinter.lang.pack['EEPROM']['Home_Offset'],
                                                              'command': 'M206',
                                                              'order': ['Z'],
                                                              'range': [10, 0.01, 0.1, 1],
                                                              'values': pconsole.home_offset
                                                             },

            roboprinter.lang.pack['EEPROM']['Probe_Offset'] : {'name': roboprinter.lang.pack['EEPROM']['Probe_Offset'],
                                                               'command': 'M851',
                                                               'order': ['Z'],
                                                               'range': [10, 0.01, 0.1, 1],
                                                               'values': pconsole.probe_offset
                                                              },

            roboprinter.lang.pack['EEPROM']['Feed_Rates']: {'name': roboprinter.lang.pack['EEPROM']['Feed_Rates'],
                                                            'command': 'M203',
                                                            'order': ['X', 'Y', 'Z', 'E', 'T0 E', 'T1 E'],
                                                            'range': [0.01, 0.1, 1, 10],
                                                            'values': pconsole.feed_rate
                                                           },

            roboprinter.lang.pack['EEPROM']['PID_Settings'] : { 'name': roboprinter.lang.pack['EEPROM']['PID_Settings'],
                                                                'command': 'M301',
                                                                'order' : ['P', 'I', 'D'],
                                                                'range' : [0.01, 0.1, 1, 10],
                                                                'values': pconsole.PID
                                                              },

            roboprinter.lang.pack['EEPROM']['Bed_PID']: { 'name': roboprinter.lang.pack['EEPROM']['Bed_PID'],
                                                          'command': 'M304',
                                                          'order' : ['P', 'I', 'D'],
                                                          'range' : [0.01, 0.1, 1, 10],
                                                          'values': pconsole.BPID
                                                        },

            roboprinter.lang.pack['EEPROM']['Steps_Unit'] : { 'name': roboprinter.lang.pack['EEPROM']['Steps_Unit'],
                                                              'command': 'M92',
                                                              'order': ['X', 'Y', 'Z', 'E', 'T0 E', 'T1 E'],
                                                              'range': [0.01, 0.1, 1, 10],
                                                              'values': pconsole.steps_per_unit
                                                            },

            roboprinter.lang.pack['EEPROM']['Accelerations'] : { 'name': roboprinter.lang.pack['EEPROM']['Accelerations'],
                                                                 'command': 'M204',
                                                                 'order': ['P', 'R', 'T'],
                                                                 'range': [0.01, 0.1, 1, 10, 100, 1000],
                                                                 'values': pconsole.accelerations
                                                               },

            roboprinter.lang.pack['EEPROM']['Max_Accelerations'] : { 'name': roboprinter.lang.pack['EEPROM']['Max_Accelerations'],
                                                                     'command': 'M201',
                                                                     'order': ['X', 'Y', 'Z', 'E', 'T0 E', 'T1 E'],
                                                                     'range': [0.01, 0.1, 1, 10, 100, 1000],
                                                                     'values': pconsole.max_accelerations
                                                                    },

            roboprinter.lang.pack['EEPROM']['Advanced']: { 'name': roboprinter.lang.pack['EEPROM']['Advanced'],
                                                           'command': 'M205',
                                                           'order': ['S', 'T', 'X', 'Y', 'Z', 'E'],
                                                           'range': [0.01, 0.1, 1, 10, 100],
                                                           'values': pconsole.advanced_variables
                                                         },
            roboprinter.lang.pack['EEPROM']['Linear_Advanced']: { 'name': roboprinter.lang.pack['EEPROM']['Linear_Advanced'],
                                                                  'command': 'M900',
                                                                  'order': ['K','R'],
                                                                  'range': [0.01, 0.1, 1, 10, 100],
                                                                  'values': pconsole.linear_advanced
                                                         },
            roboprinter.lang.pack['EEPROM']['Reset']: { 'name': roboprinter.lang.pack['EEPROM']['Reset'],
                                                        'action': self.reset_defaults,
                                                        'values': ''

                                                      },

        }

    #this function will query the eeprom when the user backs out or applys a change to the eeprom
    def refresh_list(self, *args, **kwargs):
        pconsole.query_eeprom()
        self.EEPROM_screen.repopulate_for_new_screen()
        Clock.schedule_once(self.update_title, 0.0)
        
    #this function updates the title when backing out of the change value screen
    def update_title(self, *args, **kwargs):
        self.bb.update_title(self.EEPROM_Node.title)

    def open_eeprom_value(self, setting_data):
        pconsole.dict_logger(setting_data)
        change_value_screen = Change_Value(setting_data, self.bb.back_function)
        change_value_screen.change_screen_event = self.refresh_list

        self.bb.make_screen(change_value_screen,
                            title = "Change Value",
                            option_function='no_option')

    def reset_defaults(self):

        #get the current screen
        back_screen = roboprinter.robosm.current

        def reset():
            roboprinter.printer_instance._printer.commands("M502")
            roboprinter.printer_instance._printer.commands("M500")
            roboprinter.printer_instance._printer.commands("M501")

            #make screen to say that the variables have been reset

            #body_text, button_function, button_text = roboprinter.lang.pack['Button_Screen']['Default_Button']
            content = Button_Screen(roboprinter.lang.pack['EEPROM']['Acknowledge_Reset']['Body_Text'],
                                    roboprinter.robosm.go_back_to_main,
                                    button_text = roboprinter.lang.pack['EEPROM']['Acknowledge_Reset']['Button'])

            #make screen
            roboprinter.robosm._generate_backbutton_screen(name='ack_reset_eeprom', 
                                                           title = roboprinter.lang.pack['EEPROM']['Acknowledge_Reset']['Title'] , 
                                                           back_destination=back_screen, 
                                                           content=content)

        def cancel():
            roboprinter.robosm.current = back_screen

        #make the confirmation screen
        #body_text, option1_text, option2_text, option1_function, option2_function
        content = Modal_Question_No_Title(roboprinter.lang.pack['EEPROM']['Reset_Confirmation']['Body_Text'],
                                          roboprinter.lang.pack['EEPROM']['Reset_Confirmation']['positive'],
                                          roboprinter.lang.pack['EEPROM']['Reset_Confirmation']['negative'],
                                          reset,
                                          cancel) 

        #make screen
        roboprinter.robosm._generate_backbutton_screen(name='reset_eeprom', 
                                                       title = roboprinter.lang.pack['EEPROM']['Reset_Confirmation']['Title'] , 
                                                       back_destination=back_screen, 
                                                       content=content)

    def open_setting(self, setting_data):
        if 'order' in setting_data and 'values' in setting_data:
            #order acts like a filter for what we want the user to see.
            filtered_data = []
            for setting in setting_data['order']:
                if setting in setting_data['values']:
                    data = {
                            'name': setting + ": ",
                            'setting': setting,
                            'data': setting_data
                    }
                    filtered_data.append(data)
                else:
                    Logger.info(str(setting) + " is not in the values list.")
        elif 'action' in setting_data:
            setting_data['action']()
            return #exit this function
        else:
            Logger.info("No Values or Order!")
            pconsole.dict_logger(setting_data)

        #update Node
        self.EEPROM_Node = EEPROM_Node(data=filtered_data, title = setting_data['name'], prev_data=self.EEPROM_Node)

        #update EEPROM list
        self.EEPROM_screen.eeprom_list = self.EEPROM_Node.data
        self.EEPROM_screen.repopulate_for_new_screen()

        #update callback
        self.EEPROM_screen.update_callback(self.open_eeprom_value)

        #update title
        self.bb.update_title(setting_data['name'])

    def previous_list(self):
        Logger.info("Previous list hit")
        if self.EEPROM_Node.return_previous() != None:
            #return the node to the previous node
            self.EEPROM_Node = self.EEPROM_Node.return_previous()

            #refresh the list 
            self.EEPROM_screen.eeprom_list = self.EEPROM_Node.data
            self.EEPROM_screen.repopulate_for_new_screen()
    
            #update callback
            self.EEPROM_screen.update_callback(self.open_setting)
            #update title
            self.bb.update_title(self.EEPROM_Node.title) #restore the title associated with the list
        else:
            #If there is no where left to go then go back to the previous screen in the wizard bb node list
            self.bb.update_back_function(self.bb.back_function_flow)
            self.bb.back_function_flow()


#Linked list to keep track of the EEPROM list
class EEPROM_Node(object):
    data=None
    def __init__(self, data=None, title=None, prev_data=None):
        super(EEPROM_Node, self).__init__()
        self.data = data
        self.title = title
        self.prev_data = prev_data

    def return_previous(self):
        return self.prev_data





