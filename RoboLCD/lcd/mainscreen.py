# -*- coding: utf-8 -*-
# @Author: Matt Pedler
# @Date:   2017-09-19 11:46:30
# @Last Modified by:   Matt Pedler
# @Last Modified time: 2017-12-06 13:04:38

from kivy.uix.screenmanager import Screen
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelHeader
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.graphics import RoundedRectangle
from kivy.clock import Clock
from kivy.logger import Logger
from pconsole import pconsole
from .. import roboprinter
from multiprocessing import Process
from RoboLCD.lcd import mainscreen_info

DEFAULT_FONT = 'Roboto'


class MainScreen(Screen):
    """
    Represents the the main screen template with 3 tab buttons on the top bar: Files, Printer, and Settings

    Is in charge of orchestrating content update for all 3 tabs
    """
    lang = roboprinter.lang

    def __init__(self, **kwargs):
        super(MainScreen, self).__init__(**kwargs)        


    def query_eeprom(self):
        if not roboprinter.printer_instance._printer.is_printing():

            pconsole.query_eeprom()  

    def update_file_sizes(self):
        self.ids.files_content.update_file_sizes()      

    
    def open_tab(self, tab_id):
        t = self.ids[tab_id]
        #Logger.info('Tab: {}'.format(t))
        self.ids.mstp.switch_to(t)


    def update_tab(self,tab):
        roboprinter.open_tab = tab

class MainScreenTabbedPanel(TabbedPanel):
    """
    Represents the tabbed panels. Handles toggling between FilesTab, PrinterStatusTab and SettingsTab
    """

    def __init__(self, **kwargs):
        super(MainScreenTabbedPanel, self).__init__(**kwargs)







