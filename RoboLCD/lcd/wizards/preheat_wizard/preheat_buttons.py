# -*- coding: utf-8 -*-
# @Author: Matt Pedler
# @Date:   2017-10-05 12:25:38
# @Last Modified by:   Matt Pedler
# @Last Modified time: 2017-10-27 13:23:28
# -*- coding: utf-8 -*-

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

#Python
from functools import partial
import thread

#This is just a simple button for the different options. It has a large title and a small body text
class Preheat_Button(Button):
    title = StringProperty('')
    value = ObjectProperty('')
    text_value = StringProperty('')
    body_text = StringProperty('')
    picture_source = StringProperty('')
    callback = ObjectProperty(None)
    dual = BooleanProperty(False)
    celsius = StringProperty(lang.pack['Preheat']['Celsius_Alone'])
    def __init__(self, title, value, body_text, callback):
        super(Preheat_Button, self).__init__()
        self.title = title
        self.value = value
        self.body_text = body_text
        self.callback = callback

    def update_value(self, value):
        self.value = value

    def on_value(self, instance, value):
        #Logger.info("on_value Fired: " + str(instance) + " " + str(value))

        if type(value) == str:
            self.text_value = str(value)
        else:
            self.text_value = str(value) + self.celsius

    def execute_callback(self):
        self.callback(self.value, self.title)

class Dual_Button(BoxLayout):
    def __init__(self, button_list):
        super(Dual_Button, self).__init__()
        for button in button_list:
            self.add_widget(button)

#this is a simple button that can be added anywhere
class Simple_Button(Button):
    button_text = StringProperty('')
    background_normal = StringProperty('')
    callback = ObjectProperty(None)

    def __init__(self, button_text, background_normal, callback):
        self.button_text = button_text
        self.background_normal = background_normal
        self.callback = callback
        super(Simple_Button, self).__init__()
