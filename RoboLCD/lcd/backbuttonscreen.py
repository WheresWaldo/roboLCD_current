# -*- coding: utf-8 -*-
# @Author: Matt Pedler
# @Date:   2017-07-14 12:42:48
# @Last Modified by:   Matt Pedler
# @Last Modified time: 2017-10-27 13:12:06
from kivy.uix.screenmanager import Screen
from kivy.properties import ObjectProperty, StringProperty
from .. import roboprinter
from kivy.logger import Logger


class BackButtonScreen(Screen):
    """
    The BackButtonScreen consists of 4 properties: name, title, back_destination, and content.
    It provides a template for all aestheticaly related screens. It is the job of the caller to populate this class with the correct properties thatyou want to display on the screen. Content is an object property which can be populated with whatever hierarchy of widgets you want. They will be added to a ScrollView.
    """

    name = StringProperty('--')
    content = ObjectProperty(None)
    title = StringProperty('--')
    back_destination = StringProperty('--')
    cta = ObjectProperty(None)
    icon = StringProperty('Icons/rounded_black.png')

    def __init__(self, name, title, back_destination, content, backbutton_callback=None,**kwargs):
        super(BackButtonScreen, self).__init__()
        self.name = name
        self.title = title
        self.back_destination = back_destination
        self.content = content
        self.backbutton_callback = None
        if backbutton_callback != None:
            self.backbutton_callback = backbutton_callback

        if kwargs.has_key('cta'):
            self.cta = kwargs['cta']
            self.icon = kwargs['icon']
        else:
            self.cta = self.cta_placeholder

        Logger.info(self.name)
    def cta_placeholder(self):
        return False

    def populate_layout(self):
        # adds the self.content widget to the layout that is defined in the .kv
        self.ids.content_layout.add_widget(self.content)


    def back_button(self, *args, **kwargs):
        if self.backbutton_callback != None:
            self.backbutton_callback()

        