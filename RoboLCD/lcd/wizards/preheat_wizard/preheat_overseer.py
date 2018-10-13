# -*- coding: utf-8 -*-
# @Author: Matt Pedler
# @Date:   2017-10-05 12:09:21
# @Last Modified by:   Matt Pedler
# @Last Modified time: 2018-01-31 12:08:24


#kivy
from kivy.uix.button import Button
from kivy.properties import StringProperty, NumericProperty, ObjectProperty, BooleanProperty
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.uix.togglebutton import ToggleButton
from kivy.logger import Logger
from kivy.clock import Clock

#RoboLCD
from RoboLCD import roboprinter
from RoboLCD.lcd.pconsole import pconsole
from RoboLCD.lcd.printer_jog import printer_jog
from RoboLCD.lcd.scrollbox import Scroll_Box_Even
from RoboLCD.lcd.Language import lang
from RoboLCD.lcd.common_screens import Modal_Question_No_Title, KeyboardInput, Keypad, Extruder_Selector
from RoboLCD.lcd.session_saver import session_saver
from RoboLCD.lcd.connection_popup import Info_Popup, Error_Popup

from RoboLCD.lcd.wizards.preheat_wizard.option_view import Option_View
from RoboLCD.lcd.wizards.preheat_wizard.preheat import Preheat

#Python
from functools import partial
import thread
import gc


#This class oversees all of the preheat screens. All callbacks eventually lead back here.
class Preheat_Overseer(object):
    dual = False
    def __init__(self, end_point=None, dual = False, back_button_screen = None, group=None, **kwargs):
        self.model = roboprinter.printer_instance._settings.get(['Model'])
        self._name = kwargs['name']
        self.title = kwargs['title']
        self.back_destination = kwargs['back_destination']
        self.end_point = end_point
        self.dual = dual
        # self.c = None
        self.debug_mode = False

        #set the make screen function. If this is None then we will generate the screen in the old Back Button format
        self.bb = back_button_screen
        self.group = group

        if self.dual:
            self.show_dual_preheat_selection_screen()
        else:
            self.show_preheat_selection_screen()

    def cleanup(self):
        Logger.info("Deleting preheat_overseer")
        #self.c.cleanup()
        del_list = []
        for self_var in self.__dict__:
            del_list.append(self_var)
        for self_var in del_list:
            #Logger.info("Deleting " + str(self_var))
            del self.__dict__[self_var]

        #Tell Self to print out any remaining referrers 
        # Logger.info("---> Printing referrers of Preheat_Overseer")
        # gc.collect()
        # for referer in gc.get_referrers(self):
        #     Logger.info(referer)
        # Logger.info("---> Done printing referrers of Preheat_Overseer")

        del self

    #This will create the preheat selection screen.
    def show_preheat_selection_screen(self,*args, **kwargs):
        acceptable_selections = roboprinter.printer_instance._settings.get(['Temp_Preset'])
        #populate with some default values if acceptable_selections == 0
        Logger.info("selection count = " + str(len(acceptable_selections)))
        if len(acceptable_selections) == 0:
            Logger.info("Returning to Defaults")
            self.add_defaults()



        if self.bb == None:
            self.c = Preheat(self.switch_to_preheat)
            roboprinter.robosm._generate_backbutton_screen(name=self._name,
                                                           title=self.title ,
                                                           back_destination=self.back_destination,
                                                           content=self.c,
                                                           cta=self.create_preset,
                                                           icon='Icons/Preheat/add_preset.png',
                                                           )
        else:

            if not self.bb.does_screen_exist(self.title):
                self.c = Preheat(self.switch_to_preheat)
                self.bb.make_screen(self.c,
                             self.title,
                             option_function=self.create_preset,
                             option_icon='Icons/Preheat/add_preset.png',
                             )
            else:
                self.bb.go_back_to_screen_with_title(self.title) #if this isn't the first time we made this screen then go back to the screen



    def add_defaults(self):
        default_selections = {
                                'Robo PLA':
                                {
                                    'Extruder1': 190,
                                    'Bed': 60
                                },
                                'Robo ABS':
                                {
                                    'Extruder1': 230,
                                    'Bed': 100
                                }
        }

        #save default selection
        roboprinter.printer_instance._settings.set(['Temp_Preset'], default_selections)
        roboprinter.printer_instance._settings.save()

    def show_dual_preheat_selection_screen(self, *args, **kwargs):
        acceptable_dual_selections = roboprinter.printer_instance._settings.get(['Dual_Temp_Preset'])
        #populate with some default values if acceptable_selections == 0
        Logger.info("selection count = " + str(len(acceptable_dual_selections)))
        if len(acceptable_dual_selections) == 0:
            Logger.info("Returning to Defaults")
            self.add_dual_defaults()

        if self.bb == None:

            self.c = Preheat(self.switch_to_preheat, dual=True)

            roboprinter.robosm._generate_backbutton_screen(name=self._name,
                                                           title=self.title ,
                                                           back_destination=roboprinter.robosm.current,
                                                           content=self.c,
                                                           cta=self.create_preset,
                                                           icon='Icons/Preheat/add_preset.png',
                                                           )
        else:
            if not self.bb.does_screen_exist(self.title):
                self.c = Preheat(self.switch_to_preheat, dual=True)
                self.bb.make_screen(self.c,
                             self.title,
                             option_function=self.create_preset,
                             option_icon='Icons/Preheat/add_preset.png',
                             )
            else:
                self.bb.go_back_to_screen_with_title(self.title) #if this isn't the first time we made this screen then go back to the screen

            ### FLAGGED FOR CLEAN UP
            # # Print out the instance of Preheat class. The name of the instance and
            # # address in memory will be printed.
            # Logger.info("SELF: " + str(self.c))

    def add_dual_defaults(self):
        dual_default_selections = {

                                'Robo PLA and WS Filament':
                                {
                                    'Extruder1': 190,
                                    'Extruder2': 190,
                                    'Bed': 60
                                },
                                'Robo ABS and WS Filament':
                                {
                                    'Extruder1': 230,
                                    'Extruder2': 190,
                                    'Bed': 100
                                }
        }

        #save dual defaults
        roboprinter.printer_instance._settings.set(['Dual_Temp_Preset'], dual_default_selections)
        roboprinter.printer_instance._settings.save()

    #This is a callback for the preheat selection screen. This gets called when a user clicks on a preheat option
    def switch_to_preheat(self, value, option):
        #get all temperature presets

        Logger.info("Dual is set to: " + str(self.dual))
        if self.dual:
            acceptable_selections = roboprinter.printer_instance._settings.get(['Dual_Temp_Preset'])
            #make sure the selection is a valid selection from the dictionary
            if option in acceptable_selections:
                self.generate_dual_option(option, acceptable_selections[option])
            else:
                Logger.info("Not an acceptable selection from dictionary: " + option)
        else:
            acceptable_selections = roboprinter.printer_instance._settings.get(['Temp_Preset'])
            #make sure the selection is a valid selection from the dictionary
            if option in acceptable_selections:
                self.generate_single_option(option, acceptable_selections[option])
            else:
                Logger.info("Not an acceptable selection from dictionary: " + option)


    def generate_dual_option(self, name, entry):
        title = name
        temp_ext1 = entry['Extruder1']
        temp_ext2 = entry['Extruder2']
        temp_bed = entry['Bed']
        body_text = ("[size=40][color=#69B3E7][font=fonts/S-Core - CoreSansD55Bold.otf][b]" + title + "[/color][/b][/font]\n" +
                     "[size=30]" + lang.pack['Preheat']['Extruder1'] + str(temp_ext1) + lang.pack['Preheat']['Celsius_Alone'] +
                     "\n[size=30]" + lang.pack['Preheat']['Extruder2'] + str(temp_ext2) + lang.pack['Preheat']['Celsius_Alone'] +
                     "\n" + lang.pack['Preheat']['Bed'] + str(temp_bed) + lang.pack['Preheat']['Celsius_Alone'])

        #alter the view for the model:
        if self.model == "Robo C2":
            body_text = ("[size=40][color=#69B3E7][font=fonts/S-Core - CoreSansD55Bold.otf][b]" + title + "[/color][/b][/font]\n" +
                         "[size=30]" + lang.pack['Preheat']['Extruder1'] + str(temp_ext1) + lang.pack['Preheat']['Celsius_Alone'] +
                         "\n[size=30]" + lang.pack['Preheat']['Extruder2'] + str(temp_ext2) + lang.pack['Preheat']['Celsius_Alone'] )

        #these options lead to callbacks that will either set the temperature or edit the option
        option1 = partial(self.set_temp, extruder = [temp_ext1, temp_ext2], bed = temp_bed)
        option2 = partial(self.edit, option = title)

        option1_text = lang.pack['Preheat']['Preheat']
        if self.end_point != None:
           option1_text = lang.pack['Preheat']['Select']
        #body_text, option1_text, option2_text, option1_function, option2_function
        modal_screen = Modal_Question_No_Title(body_text, option1_text, lang.pack['Preheat']['Edit'], option1, option2)

        #make screen
        if self.bb == None:
            self.bb_screen = roboprinter.robosm._generate_backbutton_screen(name='view_preheat',
                                                           title = lang.pack['Preheat']['Edit_Preset']['Select_Preset'] ,
                                                           back_destination=self._name,
                                                           content=modal_screen,
                                                           backbutton_callback=self.c.update)
        else:
            #if this screen already exists then delete it and remake it.
            if self.bb.does_screen_exist(lang.pack['Preheat']['Edit_Preset']['Select_Preset']):
                self.show_dual_preheat_selection_screen()

            self.bb.make_screen(modal_screen,
                             lang.pack['Preheat']['Edit_Preset']['Select_Preset'],
                             option_function="no_option",
                             )

    def generate_single_option(self, name, entry):
        title = name
        temp_ext1 = entry['Extruder1']
        temp_bed = entry['Bed']
        body_text = '[size=40][color=#69B3E7][font=fonts/S-Core - CoreSansD55Bold.otf][b]' + title + "[/color][/b][/font]\n[size=30]" + lang.pack['Preheat']['Extruder'] + str(temp_ext1) + lang.pack['Preheat']['Celsius_Alone'] + "\n" + lang.pack['Preheat']['Bed'] + str(temp_bed) + lang.pack['Preheat']['Celsius_Alone']

        #alter the view for the model:
        if self.model == "Robo C2":
            body_text = '[size=40][color=#69B3E7][font=fonts/S-Core - CoreSansD55Bold.otf][b]' + title + "[/color][/b][/font]\n[size=30]" + lang.pack['Preheat']['Extruder'] + str(temp_ext1) + lang.pack['Preheat']['Celsius_Alone']


        #these options lead to callbacks that will either set the temperature or edit the option
        option1 = partial(self.set_temp, extruder = temp_ext1, bed = temp_bed)
        option2 = partial(self.edit, option = title)

        option1_text = lang.pack['Preheat']['Preheat']
        if self.end_point != None:
           option1_text = lang.pack['Preheat']['Select']
        #body_text, option1_text, option2_text, option1_function, option2_function
        modal_screen = Modal_Question_No_Title(body_text, option1_text, lang.pack['Preheat']['Edit'], option1, option2)

        #make screen
        if self.bb == None:
            roboprinter.robosm._generate_backbutton_screen(name='view_preheat',
                                                           title = lang.pack['Preheat']['Edit_Preset']['Select_Preset'] ,
                                                           back_destination=self._name,
                                                           content=modal_screen,
                                                           backbutton_callback=self.c.update)

        else:
            #if this screen already exists then delete it and remake it.
            if self.bb.does_screen_exist(lang.pack['Preheat']['Edit_Preset']['Select_Preset']):
                self.show_preheat_selection_screen()

            self.bb.make_screen(modal_screen,
                             lang.pack['Preheat']['Edit_Preset']['Select_Preset'],
                             option_function="no_option",
                             )


    #This will either set the temp or execute the callback to a custon end point
    def set_temp(self, extruder, bed):
        #Go back to the printer status tab, or call a custom callback to go to a new screen
        if self.end_point == None:

            if type(extruder) != list:
                roboprinter.printer_instance._printer.set_temperature('tool0', float(extruder))
                roboprinter.printer_instance._printer.set_temperature('bed', float(bed))
                Logger.info("Set temperature to extruder: " + str(extruder) + " set temp to bed: " + str(bed))
                session_saver.saved['Move_Tools']('TEMP')
                roboprinter.robosm.go_back_to_main('printer_status_tab')
            else:
                roboprinter.printer_instance._printer.set_temperature('tool0', float(extruder[0]))
                roboprinter.printer_instance._printer.set_temperature('tool1', float(extruder[1]))
                roboprinter.printer_instance._printer.set_temperature('bed', float(bed))
                Logger.info("Set temperature to extruder1: " + str(extruder[0]) + " extruder2: " + str(extruder[1]) + " set temp to bed: " + str(bed))
                session_saver.saved['Move_Tools']('TEMP')
                roboprinter.robosm.go_back_to_main('printer_status_tab')
        else:
            self.end_point(extruder, bed)


    #This sets up the screen for editing an option
    def edit(self, option):

        if not self.dual:
            delete_callback = self.show_preheat_selection_screen
        else:
            delete_callback = self.show_dual_preheat_selection_screen
        Logger.info("option: " + str(option))
        if self.bb == None:
            content = Option_View(option=option,
                              dual = self.dual,
                              callback = self.switch_to_preheat,
                              delete_callback = delete_callback,
                              back_destination = roboprinter.robosm.current)
            roboprinter.robosm._generate_backbutton_screen(name='edit_preheat',
                                                           title = lang.pack['Preheat']['Edit_Preset']['Title'] ,
                                                           back_destination=roboprinter.robosm.current,
                                                           content=content)
        else:
            Logger.info("Making Option_View with group: " + str(self.group))
            content = Option_View(option=option,
                              dual=self.dual,
                              callback = self.switch_to_preheat,
                              delete_callback = delete_callback,
                              back_destination = roboprinter.robosm.current,
                              back_button_screen=self.bb,
                              group=self.group)
            self.bb.make_screen(content,
                             lang.pack['Preheat']['Edit_Preset']['Title'],
                             option_function='no_option',
                             group=self.group)

    #This sets up the screen to create a custom preset
    def create_preset(self):
        Logger.info("Create new preset")
        if not self.dual:
            callback = self.show_preheat_selection_screen
        else:
            callback = self.show_dual_preheat_selection_screen

        if self.bb == None:
            content = Option_View(callback = callback,
                                  dual=self.dual)
            roboprinter.robosm._generate_backbutton_screen(name='edit_preheat',
                                                           title = lang.pack['Preheat']['Edit_Preset']['Add_Material'] ,
                                                           back_destination=roboprinter.robosm.current,
                                                           content=content)
        else:
            content = Option_View(callback = callback,
                                  dual=self.dual,
                                  back_button_screen=self.bb,
                                  group=self.group)
            self.bb.make_screen(content,
                             lang.pack['Preheat']['Edit_Preset']['Add_Material'] ,
                             option_function='no_option',
                             group=self.group)
