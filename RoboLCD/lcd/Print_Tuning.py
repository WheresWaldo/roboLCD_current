# -*- coding: utf-8 -*-
# @Author: Matt Pedler
# @Date:   2017-07-14 12:42:48
# @Last Modified by:   Matt Pedler
# @Last Modified time: 2017-10-27 13:14:51
from kivy.uix.button import Button
from kivy.properties import StringProperty, NumericProperty, ObjectProperty, BooleanProperty
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.uix.togglebutton import ToggleButton
from .. import roboprinter
from functools import partial
from kivy.logger import Logger
from kivy.clock import Clock
from session_saver import session_saver

class Tuning_Overseer(object):
    """docstring for Tuning_Overseer"""
    def __init__(self):
        super(Tuning_Overseer, self).__init__()
        
    def tuning_object(self):
        current_data = roboprinter.printer_instance._printer.get_current_data()
        is_printing = current_data['state']['flags']['printing']
        is_paused = current_data['state']['flags']['paused']

        if (is_printing or is_paused):
            return Print_Tuning()
        elif not is_printing and not is_paused:
            return Print_Tuning(fan_only=True)
                  


class Print_Tuning(BoxLayout):

    lang = roboprinter.lang

    tuning_number = StringProperty('[size=30]999')
    title_label_text = StringProperty('[size=40][color=#69B3E7]' + lang.pack['Print_Tuning']['Fan_Speed'] + '[/color][/size]')
    up_icon = StringProperty("Icons/Tuning/bigger_icons/up_1.png")
    down_icon = StringProperty("Icons/Tuning/bigger_icons/down_1.png")

    flow_rate_number = NumericProperty(100)
    feed_rate_number = NumericProperty(100)
    fan_speed_number = NumericProperty(0)

    change_amount_value = [1,10]
    change_icon_up = ["Icons/Tuning/bigger_icons/up_1.png", "Icons/Tuning/bigger_icons/up_10.png"]
    change_icon_down = ["Icons/Tuning/bigger_icons/down_1.png", "Icons/Tuning/bigger_icons/down_10.png"]
    change_increment = ["Icons/Tuning/bigger_icons/increment_1.png", "Icons/Tuning/bigger_icons/increment_10.png"]
    change_value = NumericProperty(0)

    blue_color = [0.41015625, 0.69921875, 0.90234375, 1]
    black_color = [0.0,0.0,0.0,0.0]
    white_color = [1,1,1,1]

    #button color
    fan_color = ObjectProperty([0,0,0,0])
    feed_color = ObjectProperty([0,0,0,0])
    flow_color = ObjectProperty([0,0,0,0])

    #button backgroud color
    fan_button_color = StringProperty("Icons/white_outline.png")
    feed_button_color = StringProperty("Icons/white_outline.png")
    flow_button_color = StringProperty("Icons/white_outline.png")

    white_outline = "Icons/white_outline.png"
    blue_outline = "Icons/blue_button_style.png"

    #button icon
    fan_button_icon = StringProperty("Icons/Tuning/New Tuning/Fan speed.png")
    feed_button_icon = StringProperty("Icons/Tuning/New Tuning/Print speed.png")
    flow_button_icon = StringProperty("Icons/Tuning/New Tuning/Flow rate.png")

    fan_icons = ["Icons/Tuning/New Tuning/Fan speed.png", "Icons/Tuning/New Tuning/Fan speed active.png"]
    feed_icons = ["Icons/Tuning/New Tuning/Print speed.png", "Icons/Tuning/New Tuning/Print speed active.png"]
    flow_icons = ["Icons/Tuning/New Tuning/Flow rate.png", "Icons/Tuning/New Tuning/Flow rate active.png"]

    fan_only = BooleanProperty(False)

    def __init__(self, fan_only=False, **kwargs):
        super(Print_Tuning, self).__init__(**kwargs)
        self.fan_only = fan_only
        self.flow_active = False
        self.feed_active = False
        self.fan_active = True
        self.tune_rates = {'FLOW': self.flow_rate_number, 
                           'FEED': self.feed_rate_number, 
                           'FAN': self.fan_speed_number}
        self.load_tuning_info()
        self.current_tuner = 'FAN'
        self.fan_button()

        self.max_rates = {'FLOW': 125,
                          'FEED': 200,
                          'FAN': 100}

        self.min_rates = {'FLOW': 75,
                          'FEED': 50,
                          'FAN': 0}

    
    def add_button(self, amount):
        self.tune_rates[self.current_tuner] += amount
        if self.tune_rates[self.current_tuner] in range(self.min_rates[self.current_tuner], self.max_rates[self.current_tuner]):
            self.tuning_number = str(self.tune_rates[self.current_tuner])

        elif self.tune_rates[self.current_tuner] > self.max_rates[self.current_tuner]:
            self.tune_rates[self.current_tuner] = self.max_rates[self.current_tuner]
            self.tuning_number = str(self.tune_rates[self.current_tuner])

        elif self.tune_rates[self.current_tuner] < self.min_rates[self.current_tuner]:
            self.tune_rates[self.current_tuner] = self.min_rates[self.current_tuner]
            self.tuning_number = str(self.tune_rates[self.current_tuner])

        self.apply_tunings()
        self.save_tuning_info()

    def flow_button(self):
        self.set_active('FLOW')
        self.title_label_text = "[size=40][color=#69B3E7]" + roboprinter.lang.pack['Print_Tuning']['Flow_Rate'] + "[/size][/color]"
        self.save_tuning_info()

    def feed_button(self):
        self.set_active('FEED')
        self.title_label_text = "[size=40][color=#69B3E7]" + roboprinter.lang.pack['Print_Tuning']['Printing_Speed'] + "[/size][/color]"
        self.save_tuning_info()

    def fan_button(self):
        self.set_active('FAN')
        self.title_label_text = "[size=40][color=#69B3E7]" + roboprinter.lang.pack['Print_Tuning']['Fan_Speed'] + "[/size][/color]"
        self.save_tuning_info()

    def set_active(self, tuner):
        acceptable_actives = {'FLOW': self.flow_active,
                              'FEED': self.feed_active,
                              'FAN': self.fan_active}

        

        if tuner in acceptable_actives:
            for t in acceptable_actives:
                acceptable_actives[t] = False
            acceptable_actives[tuner] = True
            self.change_active_color(tuner)
            self.current_tuner = tuner

            self.tuning_number = str(self.tune_rates[self.current_tuner])

    def change_active_color(self, tuner):
        if tuner == 'FLOW':
            #color
            self.flow_color = self.blue_color
            self.feed_color = self.black_color
            self.fan_color = self.black_color

            #icon
            self.flow_button_icon = self.flow_icons[1]
            self.fan_button_icon = self.fan_icons[0]
            self.feed_button_icon = self.feed_icons[0]
            

            #button color
            self.flow_button_color = self.blue_outline
            self.fan_button_color = self.white_outline
            self.feed_button_color = self.white_outline
            
        elif tuner == 'FEED':
            self.feed_color = self.blue_color
            self.flow_color = self.black_color
            self.fan_color = self.black_color

            #icon
            self.feed_button_icon = self.feed_icons[1]
            self.flow_button_icon = self.flow_icons[0]
            self.fan_button_icon = self.fan_icons[0]
            
            #button color
            self.feed_button_color = self.blue_outline
            self.flow_button_color = self.white_outline
            self.fan_button_color = self.white_outline
            
        elif tuner == 'FAN':
            self.fan_color = self.blue_color
            self.flow_color = self.black_color
            self.feed_color = self.black_color

            #icon
            self.fan_button_icon = self.fan_icons[1]
            self.flow_button_icon = self.flow_icons[0]
            self.feed_button_icon = self.feed_icons[0]
            

            #button color
            self.fan_button_color = self.blue_outline
            self.flow_button_color = self.white_outline
            self.feed_button_color = self.white_outline

    def save_tuning_info(self):
        session_saver.save_variable('FLOW', self.tune_rates['FLOW'])
        session_saver.save_variable('FEED', self.tune_rates['FEED'])
        session_saver.save_variable('FAN', self.tune_rates['FAN'])
        #Logger.info(str(session_saver.saved))

    def load_tuning_info(self):
        tuning_exists = False
        try:
            session_saver.saved['FLOW']
            tuning_exists = True
            Logger.info("Settings exist")
            Logger.info(str(session_saver.saved['FLOW']))
            Logger.info(str(session_saver.saved['FEED']))
            Logger.info(str(session_saver.saved['FAN']))

        except Exception as e:
            Logger.info("Settings do not exist")
            self.tune_rates['FLOW'] = 100
            self.tune_rates['FEED'] = 100
            self.tune_rates['FAN'] = 0
            
        if tuning_exists == True:
            self.tune_rates['FLOW'] =  session_saver.saved['FLOW']
            self.tune_rates['FEED'] =  session_saver.saved['FEED']
            self.tune_rates['FAN'] =  session_saver.saved['FAN']

    def apply_tunings(self):
        if self.current_tuner == 'FLOW':
            roboprinter.printer_instance._printer.flow_rate(self.tune_rates['FLOW'])
        elif self.current_tuner == 'FEED':
            roboprinter.printer_instance._printer.feed_rate(self.tune_rates['FEED'])
        elif self.current_tuner == 'FAN':
            decimal_percentage = float(self.tune_rates['FAN']) / 100.00
            fan_percentage_speed = decimal_percentage * 255 
            roboprinter.printer_instance._printer.commands('M106 S'+ str(fan_percentage_speed))

    def reset_tunings(self):
        self.tune_rates = {'FLOW': self.flow_rate_number, 
                           'FEED': self.feed_rate_number, 
                           'FAN': self.fan_speed_number}

        self.save_tuning_info()

    def change_amount(self):
        self.change_value += 1

        if self.change_value > 1:
            self.change_value = 0

        #self.ids.change_text.text = "[size=60]{}[/size]".format(self.change_amount_value[self.change_value]) 
        self.ids.increment_image.source = self.change_increment[self.change_value]
        self.ids.up_image.source = self.change_icon_up[self.change_value]
        self.ids.down_image.source = self.change_icon_down[self.change_value] 



        


  