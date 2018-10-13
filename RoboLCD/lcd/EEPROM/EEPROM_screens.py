# -*- coding: utf-8 -*-
# @Author: Matt Pedler
# @Date:   2017-10-18 15:12:00
# @Last Modified by:   Matt Pedler
# @Last Modified time: 2018-01-28 15:25:47

#Kivy
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.properties import ObjectProperty, StringProperty, BooleanProperty, NumericProperty, ListProperty
from kivy.clock import Clock
from kivy.logger import Logger
from kivy.core.window import Window


#python
import math
import os
import shutil
import re
from datetime import datetime
import collections
import traceback
from functools import partial

#RoboLCD
from RoboLCD.lcd.Language import lang
from RoboLCD.lcd.common_screens import Wizard_Screen_Controls
from RoboLCD import roboprinter
from RoboLCD.lcd.connection_popup import Status_Popup
from RoboLCD.lcd.pconsole import pconsole



'''
Scroll_Box_eeprom_list is meant to scroll through a dictionary of the files. This will save space as well as make refreshing files easier

'''
class Scroll_Box_EEPROM_List(BoxLayout, Wizard_Screen_Controls):
    """docstring for Scroll_Box_Even"""
    position = 0
    max_pos = 0
    buttons = []
    up_icons = ["Icons/Up-arrow-grey.png", "Icons/Up-arrow-blue.png"]
    down_icons = ["Icons/Down-arrow-grey.png", "Icons/Down-arrow-blue.png"]
    up_icon = ObjectProperty("Icons/Up-arrow-grey.png")
    down_icon = ObjectProperty("Icons/Down-arrow-grey.png")
    callback = ObjectProperty(None)
    def __init__(self, eeprom_list, button_callback, **kwargs):
        super(Scroll_Box_EEPROM_List, self).__init__(**kwargs)
        self.up_event = None
        self.down_event = None
        self.grid = self.ids.content
        self.max_pos = len(eeprom_list) - 4
        self.eeprom_list = eeprom_list
        self.original_scroll_size = self.scroll.size_hint_x
        self.original_scroll_width = self.scroll.width
        self.file_buttons = [self.ids.button_1, self.ids.button_2, self.ids.button_3, self.ids.button_4]
        self.callback = button_callback

        self.ids.button_up.bind(state=self.up_button_state)
        self.ids.button_down.bind(state=self.down_button_state)

        for button in self.file_buttons:
            button.update_callback(self.callback)
        if len(self.eeprom_list) <= 4:
            self.scroll.size_hint_x = 0
            self.scroll.width = 0.1
        self.populate_buttons()

    def update_callback(self, callback):
        for button in self.file_buttons:
            button.update_callback(callback)

    def update_button_status(self):
        for button in self.file_buttons:
            button.update()

    def repopulate_for_new_screen(self):
        self.position = 0
        self.max_pos = len(self.eeprom_list) - 4
        self.populate_buttons()

    def populate_buttons(self):
        
        for x in range(0,4):
            if self.position + x < len(self.eeprom_list):
                self.file_buttons[x].update_file_data(self.eeprom_list[self.position + x])
            else:
                self.file_buttons[x].update_file_data(None)

        self.check_for_scroll()

    def up_button_state(self, instance, value):
        if value == 'down':
            self.on_up_press()
        else:
            self.on_up_release()


    def up_button(self):
        # Logger.info("Up hit")
        self.position -= 1
        if self.position < 0:
            self.position = 0
            self.up_event.cancel()
        self.populate_buttons()

    #every 0.2 seconds scroll up until the user releases the button
    def on_up_press(self):

        #change Color
        self.up_icon = self.up_icons[1]

        if self.up_event != None:
            self.up_event.cancel()
        if self.down_event != None:
            self.down_event.cancel()
        self.up_event = Clock.schedule_interval(self.on_up_clock, 0.2)


    def on_up_release(self):
        #change Color
        self.up_icon = self.up_icons[0]
        self.up_event.cancel()
        self.up_button()

    def on_up_clock(self,dt):
        self.up_button()

    def down_button_state(self, instance, value):
        if value == 'down':
            self.on_down_press()
        else:
            self.on_down_release()
        

    def down_button(self):
        # Logger.info("down hit")
        self.position += 1
        if self.position > self.max_pos:
            self.position = self.max_pos
            self.down_event.cancel()
        self.populate_buttons()

    #every 0.2 seconds scroll down until the user releases the button
    def on_down_press(self):
        #change Color
        self.down_icon = self.down_icons[1]
        if self.up_event != None:
            self.up_event.cancel()
        if self.down_event != None:
            self.down_event.cancel()
        self.down_event = Clock.schedule_interval(self.on_down_clock, 0.2)

    def on_down_release(self):
        #change Color
        self.down_icon = self.down_icons[0]
        self.down_event.cancel()
        self.down_button()

    def on_down_clock(self, dt):
        self.down_button()

    def check_for_scroll(self):
        if len(self.eeprom_list) <= 4:
            self.scroll.size_hint_x = 0
            self.scroll.width = 0.1
        else:
            self.scroll.size_hint_x = self.original_scroll_size
            self.scroll.width = self.original_scroll_width


class EEPROM_Button(Button, object):
    """docstring for EEPROM_Button"""

    name = StringProperty("")
    value = StringProperty("")
    callback = ObjectProperty(None)
    _setting_data = None


    def __init__(self, setting_data = None, callback = None, **kwargs):
        super(EEPROM_Button, self).__init__(**kwargs)
        self.setting_data = setting_data
        self.callback = callback

    def update_file_data(self, setting_data):
        if setting_data != None:

            self.setting_data = setting_data
            self.name = self.setting_data['name']
            if 'data' in self.setting_data:
                self.value = str(self.setting_data['data']['values'][self.setting_data['setting']])
                Logger.info(str(self.setting_data['setting']) + ": " + str(self.setting_data['data']['values'][self.setting_data['setting']]))
            else:
                self.value = ""

        else:
            self.setting_data = None
            self.name = ""
            self.callback = self.callback_placeholder
            self.value = ""

    def update_callback(self, callback):
        self.callback = callback

    def update(self):
        self.update_file_data(self.setting_data)

    def update_from_pconsole(self, value):
        #only do this if we have a specific value attached to the button
        if 'data' in self.setting_data:
            #update the values, Merge the dicts so we don't have to worry about partial updates.
            #import json
            #Logger.info("Using Command: " + str(self._setting_data['data']['command']))
            #Logger.info("Old Values: " + str(json.dumps(self.setting_data['data']['values'], indent=4)))
            #Logger.info("New Values: " + str(json.dumps(value, indent=4)))
            self.setting_data['data']['values'] = self.merge_dicts(self.setting_data['data']['values'],value)
            #update the text value
            self.value = str(self.setting_data['data']['values'][self.setting_data['setting']])

            #Logger.info("Updated Values: " + str(json.dumps(self.setting_data['data']['values'], indent=4)))

    def merge_dicts(self, *dict_args):
        result = {}
        for dictionary in dict_args:
            result.update(dictionary)
        return result


    def callback_caller(self):
        if self.callback != None:
            self.callback(self.setting_data)

    def callback_placeholder(self):
        pass

    @property
    def setting_data(self):
        return self._setting_data

    @setting_data.setter
    def setting_data(self, value):
        #remove the observer for the old setting data
        if self._setting_data != None:
            if 'data' in self._setting_data:
                pconsole.unregister_observer(self._setting_data['data']['command'], self.update_from_pconsole)

        #update setting data
        self._setting_data = value

        #register the callback
        if self._setting_data != None:
            if 'data' in self._setting_data:
                pconsole.register_observer(self._setting_data['data']['command'], self.update_from_pconsole)

class Change_Value(BoxLayout, Wizard_Screen_Controls):
    name = StringProperty("ERROR")
    number = StringProperty("999")
    value = NumericProperty(999)

    change_amount_value = ListProperty([0.01, 0.1, 1, 10, 100])
    change_value = NumericProperty(2)
    button_size = [200,200]

    def __init__(self, command_data, back_button):
        super(Change_Value, self).__init__()
        self.command = command_data['data']['command']
        self.value = command_data['data']['values'][command_data['setting']] 
        self.name = command_data['setting']
        self.number = "{:0.2f}".format(self.value)
        self.change_amount_value = command_data['data']['range']
        self.back_button = back_button

    def change_amount(self):
        value = self.change_value + 1
        

        if value >= len(self.change_amount_value):
            self.change_value = 0
        else:
            self.change_value += 1

        #self.ids.change_text.text = "[size=60]{}".format(self.change_amount_value[self.change_value]) 

    def add_button(self, value):
        self.value += value

        self.number = "{:0.2f}".format(self.value)

    def update_variable(self):
        update_string = self.command + " " + self.name + "{:0.2f}".format(self.value)
        roboprinter.printer_instance._printer.commands(update_string)
        roboprinter.printer_instance._printer.commands("M500")
        ep = Status_Popup(roboprinter.lang.pack['EEPROM']['Error_Title'], roboprinter.lang.pack['EEPROM']['Error_Body'])
        ep.show()
        self.back_button()

