# -*- coding: utf-8 -*-
# @Author: Matt Pedler
# @Date:   2017-10-05 10:47:32
# @Last Modified by:   Matt Pedler
# @Last Modified time: 2018-01-28 14:57:35

#kivy
from kivy.uix.button import Button
from kivy.properties import StringProperty, NumericProperty, ObjectProperty, BooleanProperty
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.widget import Widget
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

from RoboLCD.lcd.wizards.preheat_wizard.preheat_buttons import Preheat_Button, Simple_Button

#Python
from functools import partial
import thread
import gc

#This class shows all Preheat options
class Preheat(Scroll_Box_Even):
    dual = False
    def __init__(self,callback, dual = False, **kwargs):
        self.model = roboprinter.printer_instance._settings.get(['Model'])
        self.dual = dual
        self.callback = callback
        self.make_buttons()
        self.debug_mode = False
        super(Preheat, self).__init__(self.buttons)

        # Check the debug state. If true, print out a list of instances of
        # Preheat recognized by the garbage collector
        if self.debug_mode:
            Logger.info("---> Checking Preheat instances")
            obj_len = 0
            for obj in gc.get_objects():
                if isinstance(obj, Preheat):
                    obj_len += 1
                    Logger.info("GC: " + str(obj))
            Logger.info("There are " + str(obj_len/2) + " Preheat Objects active")

            # Print out the instance of this class. The name of the instance and
            # address in memory will be printed.
            Logger.info("SELF: " + str(self))

    #This will create the button list for the SBE
    def make_buttons(self):
        self.buttons = []

        if self.dual:
            preheat_settings = roboprinter.printer_instance._settings.get(['Dual_Temp_Preset'])
            ordered_presets = self.get_ordered_presets(preheat_settings)
            self.make_dual_extruder_buttons(ordered_presets, preheat_settings)

        else:
            preheat_settings = roboprinter.printer_instance._settings.get(['Temp_Preset'])
            ordered_presets = self.get_ordered_presets(preheat_settings)
            self.make_single_extruder_buttons(ordered_presets, preheat_settings)

    #This is called to update the screen with the most current preheat list
    def update(self):
        self.make_buttons()
        #populate buttons is a function in SBE
        self.populate_buttons()

    def get_ordered_presets(self, preheat_settings):
        #Order the preset list
        ordered_presets = []
        for temp_preset in preheat_settings:
            ordered_presets.append(temp_preset)
        ordered_presets = sorted(ordered_presets, key=str.lower)
        return ordered_presets


    def make_single_extruder_buttons(self, ordered_presets, preheat_settings):
        for temp_preset in ordered_presets:
            title = str(temp_preset)
            body_text = lang.pack['Preheat']['Preheat_Head'] + str(preheat_settings[temp_preset]['Extruder1']) + lang.pack['Preheat']['And_Bed'] + str(preheat_settings[temp_preset]['Bed']) + lang.pack['Preheat']['Celsius_Alone']

            #alter the view for the model:
            if self.model == "Robo C2":
                body_text = lang.pack['Preheat']['Preheat_Head'] + str(preheat_settings[temp_preset]['Extruder1']) + lang.pack['Preheat']['Celsius_Alone']


            temp_button = Preheat_Button(title,'', body_text, self.callback)
            self.buttons.append(temp_button)

    def make_dual_extruder_buttons(self, ordered_presets, preheat_settings):
        for temp_preset in ordered_presets:
            title = str(temp_preset)
            body_text = (lang.pack['Preheat']['Extruder1'] + str(preheat_settings[temp_preset]['Extruder1']) + lang.pack['Preheat']['Celsius_Alone'] + " " +
                         lang.pack['Preheat']['Extruder2'] + str(preheat_settings[temp_preset]['Extruder2']) + lang.pack['Preheat']['Celsius_Alone'] + " " +
                         lang.pack['Preheat']['Bed'] + str(preheat_settings[temp_preset]['Bed']) + lang.pack['Preheat']['Celsius_Alone'])

            #alter the view for the model:
            if self.model == "Robo C2":
                body_text = (lang.pack['Preheat']['Extruder1'] + str(preheat_settings[temp_preset]['Extruder1']) + lang.pack['Preheat']['Celsius_Alone'] + " " +
                             lang.pack['Preheat']['Extruder2'] + str(preheat_settings[temp_preset]['Extruder2']) + lang.pack['Preheat']['Celsius_Alone'])


            temp_button = Preheat_Button(title, '', body_text, self.callback)
            self.buttons.append(temp_button)

    def cleanup(self):
        Logger.info("Cleaning up a preheat object")
        del self.buttons
        self.buttons = []
        self.populate_buttons()
