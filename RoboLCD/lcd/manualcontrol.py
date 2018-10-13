# -*- coding: utf-8 -*-
# @Author: Matt Pedler
# @Date:   2017-07-14 12:42:48
# @Last Modified by:   Matt Pedler
# @Last Modified time: 2017-10-27 13:14:06
from kivy.uix.gridlayout import GridLayout
from kivy.uix.widget import Widget
from kivy.clock import Clock
from kivy.logger import Logger
from kivy.uix.screenmanager import Screen
from kivy.properties import ObjectProperty, StringProperty, BooleanProperty, NumericProperty, ListProperty
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.core.window import Window
from kivy.uix.image import Image
from kivy.graphics import *
from kivy.uix.label import Label
from connection_popup import Mintemp_Warning_Popup
from .. import roboprinter
from printer_jog import printer_jog
from kivy.logger import Logger
from pconsole import pconsole

class TemperatureControl(BoxLayout):
    current_temp = StringProperty('--')
    target_temp = StringProperty('--')
    input_temp = StringProperty('')

    desired_temp = 0

    def __init__(self, selected_tool= "TOOL1" ,**kwargs):
        super(TemperatureControl, self).__init__(**kwargs)
        acceptable_toolheads = {"TOOL1": 'tool0',
                                "TOOL2": 'tool1',
                                "BED": 'bed',
                                "tool0": 'tool0',
                                "tool1": 'tool1',
                                "bed": 'bed'}

        if selected_tool in acceptable_toolheads:
            self.selected_tool = acceptable_toolheads[selected_tool]

        else:
            Logger.info("TOOL CANNOT BE SELECTED: " + selected_tool)
            self.selected_tool = 'tool0'
        Clock.schedule_interval(self.update, .1)


    def update(self, dt):
        if self.desired_temp == 0:
            self.ids.set_cool.text = roboprinter.lang.pack['Temperature_Controls']['Cooldown']
            self.ids.set_cool.background_normal = 'Icons/blue_button_style.png'
        else:
            self.ids.set_cool.text = roboprinter.lang.pack['Temperature_Controls']['Set']
            self.ids.set_cool.background_normal = 'Icons/green_button_style.png'
        if self.current_temp == self.target_temp and self.current_temp != '--':
            self.ids.c_temp.color = 0,1,0,1
            self.ids.c_temp2.color = 0,1,0,1

        self.temperature()


        

    def temperature(self):
        temps  = roboprinter.printer_instance._printer.get_current_temperatures()
        current_temperature = ''
        
        try:
            current_temperature = [str(int(temps[self.selected_tool]['actual'])), str(int(temps[self.selected_tool]['target']))]
        except Exception as e:
            current_temperature = ['--','--']

        self.current_temp = current_temperature[0]
        self.target_temp = current_temperature[1]

    def set_temperature(self, ext):
        self.ids.c_temp.color = 1,0,0,0.8
        self.ids.c_temp2.color = 1,0,0,0.8
        if self.input_temp == '':
            temp = 0
            self.input_temp = "0"
        else:
            temp = int(self.input_temp)
            if temp > 290 and (self.selected_tool == 'tool0' or self.selected_tool == 'tool1'):
                temp = 290
                self.input_temp = "290"
                self.desired_temp = 290

            elif temp > 100 and self.selected_tool == 'bed' and float(pconsole.temperature['bed']) > 0:
                temp = 100
                self.input_temp = "100"
                self.desired_temp = 100

        
        Logger.info("Setting " + str(ext) + " to " + str(temp))
        roboprinter.printer_instance._printer.set_temperature(ext, temp )

    def add_number(self, number):

        text = str(self.desired_temp)

        if len(text) < 3:
        
            self.desired_temp = self.desired_temp * 10 + number
            self.input_temp = str(self.desired_temp)

    def delete_number(self):
        self.desired_temp = self.desired_temp / 10
        self.input_temp = str(self.desired_temp)
        

class Motor_Control(Button):
    pass
class Temperature_Control(Button):
    pass