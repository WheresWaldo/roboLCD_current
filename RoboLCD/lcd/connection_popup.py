# -*- coding: utf-8 -*-
# @Author: Matt Pedler
# @Date:   2017-07-14 12:42:48
# @Last Modified by:   Matt Pedler
# @Last Modified time: 2018-01-28 15:14:41
from RoboLCD import roboprinter
from kivy.clock import Clock
from kivy.uix.popup import Popup
from pconsole import pconsole
from kivy.uix.modalview import ModalView
from kivy.properties import StringProperty, NumericProperty, ObjectProperty
from kivy.logger import Logger
from functools import partial


class Updating_Popup(ModalView) :
    pass

class Zoffset_Warning_Popup(ModalView):
    """docstring for Zoffset_Warning_Popup(ModalView)"""
    current_z_offset = StringProperty('--')
    
    def __init__(self, _file_printer):
        super(Zoffset_Warning_Popup, self).__init__()
        self.file_printer = _file_printer

        self.current_z_offset = str(pconsole.home_offset['Z'])
        roboprinter.printer_instance._logger.info("Starting up the Zoffset Warning!")

    def update_z_offset(self):
        self.current_z_offset = str(pconsole.home_offset['Z'])
        
    def dismiss_popup(self, **kwargs):
        self.dismiss()
    def start_print_button(self, **kwargs):
        self.dismiss()
        self.file_printer.force_start_print()

    def generate_z_offset_wizard(self, *args, **kwargs):
        from RoboLCD.lcd.wizards.wizard_overseer import Wizards
        wiz = Wizards(soft_load=True, back_destination='main')
        wiz.load_wizard(generator='ZOFFSET', name=roboprinter.lang.pack['RoboIcons']['Z_Offset'])

class Update_Warning_Popup(ModalView):
    """docstring for Zoffset_Warning_Popup(ModalView)"""
    
    current_z_offset = StringProperty('--')
    body_text = StringProperty('[size=40][color=#69B3E7]' + roboprinter.lang.pack['Warning']['Update']['Sub_Title'] + '[/size][/color][size=30]' + roboprinter.lang.pack['Warning']['Update']['Body'] )
    
    def __init__(self, update_callback, unlock):
        super(Update_Warning_Popup, self).__init__()
        self.update_callback = update_callback
        self.unlock = unlock
        roboprinter.printer_instance._logger.info("Starting up the update Warning!")

    def update_z_offset(self):
        self.current_z_offset = str(pconsole.home_offset['Z'])
        
    def dismiss_popup(self, **kwargs):
        self.unlock()
        self.dismiss()
    def start_update_button(self, **kwargs):
        self.unlock()
        self.update_callback()
        self.dismiss()
       

class Mintemp_Warning_Popup(ModalView):
    current_temp = StringProperty('--')
    def __init__(self, temp):
        super(Mintemp_Warning_Popup, self).__init__()
        self.current_temp = roboprinter.lang.pack['Warning']['Mintemp'] + str(temp)
        self.open()
        Clock.schedule_once(self.popup_timer, 5)

    def popup_timer(self,dt):
        self.dismiss()

class Info_Popup(ModalView):
    error = StringProperty('Error')
    body_text = StringProperty('error')
    def __init__(self, error, body_text):
        super(Info_Popup, self).__init__()
        self.error = error
        self.body_text = body_text

    def show(self):
        self.open()

class Error_Popup(ModalView):
    error = StringProperty('Error')
    body_text = StringProperty('error')
    callback = ObjectProperty(None)
    def __init__(self, error, body_text, callback=None, **kwargs):
        super(Error_Popup, self).__init__()
        self.error = error
        self.body_text = body_text
        self.callback = callback

    def show(self):
        self.open()
       

class Warning_Popup(ModalView):
    warning = StringProperty("None")
    body_text = StringProperty("none")
    def __init__(self, warning, body_text):
        super(Warning_Popup, self).__init__()
        self.warning = warning
        self.body_text = body_text

    def show(self):
        self.open()

class Status_Popup(ModalView):
    error = StringProperty('Error')
    body_text = StringProperty('error')
    def __init__(self, error, body_text):
        super(Status_Popup, self).__init__()
        self.error = error
        self.body_text = body_text
        

    def show(self):
        self.open()
    def hide(self):
        self.dismiss()

class USB_Progress_Popup(ModalView):
    max_progress = NumericProperty(100)
    value_progress = NumericProperty(0)
    percent_progress = StringProperty(roboprinter.lang.pack['Warning']['USB_Progress']['Waiting'])
    error = StringProperty(roboprinter.lang.pack['Warning']['USB_Progress']['Error'])
    
    def __init__(self, error, max_progress):
        super(USB_Progress_Popup, self).__init__()
        self.error = error
        self.max_progress = max_progress

    def show(self):
        self.open()
    def hide(self):
        self.dismiss()

    def update_progress(self, progress):
        self.value_progress = progress

        pcent = (self.value_progress / self.max_progress) * 100
        pcent = int(pcent)

        self.percent_progress = str(pcent)+ roboprinter.lang.pack['Warning']['USB_Progress']['P_Completed']

        #map that to the progress bar

        self.value_progress = (self.value_progress / self.max_progress) * 340 #340 is the width of the progress bar
        
    def update_max(self, max_prog):
        self.max_progress = max_prog


