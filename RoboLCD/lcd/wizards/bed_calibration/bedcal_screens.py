# -*- coding: utf-8 -*-
# @Author: Matt Pedler
# @Date:   2017-12-07 16:45:53
# @Last Modified by:   Matt Pedler
# @Last Modified time: 2018-01-27 15:51:00
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

#Python
from functools import partial
class Quad_Icon_Layout(BoxLayout):
    body_text = StringProperty("Error")

    def __init__(self, bl1, bl2, body_text, **kwargs):
        super(Quad_Icon_Layout, self).__init__()
        self.body_text =  body_text
        self.bl1 = bl1
        self.bl2 = bl2
        self.alter_layout()

    def cleanup(self):
        Logger.info("Cleaning up Quad_Icon_Layout")
        super(Quad_Icon_Layout, self).cleanup()

        #remove from widget
        for button in self.bl1:
            if button.parent:
                button.parent.remove_widget(button)

        for button in self.bl2:
            if button.parent:
                button.parent.remove_widget(button)

        #clear grid
        grid = self.ids.button_grid
        grid.clear_widgets()

        #remove self from parent
        if self.parent:
            self.parent.remove_widget(self)




    def alter_layout(self):
        grid = self.ids.button_grid

        grid.clear_widgets()
       
        
        #make a 2x2 grid
        for button in self.bl1:
            grid.add_widget(button)

        for button in self.bl2:
            grid.add_widget(button)

          

