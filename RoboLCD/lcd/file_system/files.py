# -*- coding: utf-8 -*-
# @Author: Matt Pedler
# @Date:   2017-09-27 15:58:32
# @Last Modified by:   Matt Pedler
# @Last Modified time: 2018-02-22 09:43:44
#Kivy
from kivy.uix.label import Label
from kivy.uix.gridlayout import GridLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.tabbedpanel import TabbedPanelHeader
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.effects.scroll import ScrollEffect
from kivy.uix.screenmanager import Screen
from kivy.properties import ObjectProperty, StringProperty, BooleanProperty, NumericProperty
from kivy.clock import Clock
from kivy.uix.widget import Widget
from kivy.uix.popup import Popup
from kivy.logger import Logger
from kivy.core.window import Window
from kivy.uix.vkeyboard import VKeyboard

#python
import math
import os
import shutil
import re
from datetime import datetime
import collections
import subprocess
import threading
import traceback
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from functools import partial

#RoboLCD
from RoboLCD.lcd.pconsole import pconsole
from RoboLCD import roboprinter
from RoboLCD.lcd.Language import lang
from RoboLCD.lcd.scrollbox import Scroll_Box_Even, Scroll_Box_Icons, Robo_Icons, Storage_Icons
from RoboLCD.lcd.connection_popup import Zoffset_Warning_Popup, Error_Popup, USB_Progress_Popup
from RoboLCD.lcd.session_saver import session_saver
from file_explorer import File_Explorer
from file_options import FileOptions
from file_overseer import File_Overseer

#octoprint
import octoprint.filemanager

class FilesTab(TabbedPanelHeader):
    """
    Represents the Files tab header and dynamic content
    """
    pass


USB_DIR = '/home/pi/.octoprint/uploads/USB'
FILES_DIR = '/home/pi/.octoprint/uploads'
class FilesContent(BoxLayout):
    """
    This class represents the properties and methods necessary to render the dynamic components of the FilesTab

    Files Content lets the user choose between which filesystem they would prefer to browse. Then another screen
    gets pulled up and displays the chosen file system. Right now the options are Local Files and USB Files.
    """

    def __init__(self, **kwargs):
        super(FilesContent, self).__init__(**kwargs)
        self.file_lock = False
        Clock.schedule_interval(self.collect_meta_data, 0.1)

        #if octoprint has changed files then update them
        session_saver.save_variable('file_callback', self.call_to_update)
        session_saver.save_variable('usb_status', self.update_usb_status)
        session_saver.save_variable('usb_mounted', False)

        #schedule directory observer http://pythonhosted.org/watchdog/api.html#watchdog.events.FileSystemEventHandler
        self.dir_observe = Observer()
        self.callback = FileSystemEventHandler()
        self.callback.on_any_event = self.on_any_event
        self.dir_observe.schedule(self.callback, "/dev", recursive=True)
        self.dir_observe.start()

        #All new Screens will call File_Overseer
        self.file_screen = File_Overseer()
        self.USB_files_text = lang.pack['Files']['File_Tab']['USB_Files'] + "\n"

        usb_size = None
        if os.path.isdir(USB_DIR):
            if len(os.listdir(USB_DIR)) != 0:
                self.has_usb_attached = True
                session_saver.saved['usb_mounted'] = True
                usb_size = self.disk_usage(USB_DIR)
                self.USB_files_text = "[color=#69B3E7]" + lang.pack['Files']['File_Tab']['USB_Files'] + "[/color]\n( " + str(usb_size[2]) + " / " + str(usb_size[0]) + " )"
            else:
                self.has_usb_attached = False
                session_saver.saved['usb_mounted'] = False

        self.screen = self.file_screen.make_screen()

        disk = self.disk_usage(os.getcwd())
        local_files = lang.pack['Files']['File_Tab']['Local_Files'] + "\n( " + str(disk[2]) + " / " + str(disk[0]) + " )" 

        #make content for the screen 
        self.local_button = Storage_Icons('Icons/Files_Icons/File_Options/Local Storage.png', local_files, "LOCAL", callback=self.open_file_system)
        self.usb_button = Storage_Icons('Icons/Files_Icons/File_Options/USB Storage.png', self.USB_files_text, "USB", callback=self.open_file_system)
        #change the state of the USB button
        

        self.usb_button.button_state = not self.has_usb_attached

        files = Scroll_Box_Icons([self.local_button, self.usb_button])
        self.clear_widgets()
        self.add_widget(files)


        self.update_files()

    def update_file_sizes(self):
        
        if 'file_callback' in session_saver.saved:
            session_saver.saved['file_callback']()


    
    def get_size(self, size):
        system = [
                 (1024 ** 5, ' PB'),
                 (1024 ** 4, ' TB'), 
                 (1024 ** 3, ' GB'), 
                 (1024 ** 2, ' MB'), 
                 (1024 ** 1, ' KB'),
                 (1024 ** 0, ' b'),
                 ]

        for factor, suffix in system:
            if size >= factor:
                break
        amount = float(float(size)/float(factor))
        return str("{0:0.1f}".format(amount)) + suffix

    def disk_usage(self,path):
        st = os.statvfs(path)
        free = st.f_bavail * st.f_frsize
        total = st.f_blocks * st.f_frsize
        used = (st.f_blocks - st.f_bfree) * st.f_frsize
        return [self.get_size(int(total)), self.get_size(int(free)), self.get_size(int(used))]

    # This seems like a roundabout way to call 'update_files' However if it is not called in this way 
    # Graphical issues become present. It is called in this way to make the request come from the 
    # thread kivy is on
    def call_to_update(self):
        Clock.schedule_once(self.call_to_update2, 0.01)
    def call_to_update2(self ,dt):
        self.update_files()

    def open_file_system(self, generator=None, name=None):
        #go to root directory
        self.file_screen.goto_root()
        
        #if we want to go to the usb then populate the USB
        if generator == "USB":
            #make the USB screen
            self.file_screen.goto_USB()

        #populate a new screen
        #Logger.info("Opening screen")

        self.screen.delete_same_name_screens()
        roboprinter.robosm.add_widget(self.screen)
        roboprinter.robosm.current = self.screen.name

    def update_files(self):
        
        #figure out disk sizes
        disk = self.disk_usage(os.getcwd())
        disk_size = "( " + str(disk[2]) + " / " + str(disk[0]) + " )"
        local_files = lang.pack['Files']['File_Tab']['Local_Files'] + "\n" + str(disk_size) 
        
        if session_saver.saved['usb_mounted']:
            usb_size = self.disk_usage(USB_DIR)
            usb_disk_size ="( " + str(usb_size[2]) + " / " + str(usb_size[0]) + " )"
            Logger.info("Evaluating disk size")
            #if the USB_DIR is not a mount point, then there is not a USB available or the USB is a NTFS file system
            if not os.path.ismount(USB_DIR):
                Logger.info("USB_DIR is not a mounted path! Putting warning in text!")
                self.USB_files_text = lang.pack['Files']['File_Tab']['Unmounted_USB']
                self.usb_button.button_state = True
            else:
                Logger.info("USB is a mounted path, making connected text")
                self.USB_files_text = "[color=#69B3E7]" + lang.pack['Files']['File_Tab']['USB_Files'] + "[/color]\n" + str(usb_disk_size)
        else:
            Logger.info("USB is not connected Greying out button")
            self.USB_files_text = lang.pack['Files']['File_Tab']['USB_Files'] + "\n"

        #Update USB text
        self.usb_button.original_icon_name = self.USB_files_text
        self.usb_button.icon_name = self.USB_files_text

        self.local_button.original_icon_name = local_files
        self.local_button.icon_name = local_files    
        

    #This function is a callback from an observer that is watching /dev for any device changes. Namely the USB being plugged in
    def on_any_event(self, event):
        usb_path = "/dev/sd"
        extern = re.match(usb_path, event.src_path)

        if extern != None and event.src_path.endswith('1'):

            if event.event_type == 'deleted':
                Logger.info("USB Removed " + event.src_path)
                session_saver.saved['usb_mounted'] = False
                self.has_usb_attached = False
                self.call_to_update()


            elif event.event_type == 'created':
                Logger.info("USB Plugged in " + event.src_path)
                session_saver.saved['usb_mounted'] = True
                session_saver.saved['usb_location'] = event.src_path
                self.has_usb_attached = True
                self.call_to_update()

            #change the state of the USB button if it is mounted
            if os.path.ismount(USB_DIR):
                self.usb_button.button_state = not self.has_usb_attached
            else:
                self.usb_button.button_state = True

            #update the socket to tell the rest of the world the USB status.
            # usb_attached means that the USB is attached, usb mounted means that the usb is readable by the system.
            usb_dict = {
                'usb_attached': self.has_usb_attached,
                'usb_mounted': not self.usb_button.button_state #originally this variable means "is_disabled?" so flip it to make sense to us
            }
            roboprinter.printer_instance._plugin_manager.send_plugin_message(roboprinter.printer_instance._identifier, dict(type="usb_status", data=usb_dict))
    

    def update_usb_status(self):
        #update the socket to tell the rest of the world the USB status.
        # usb_attached means that the USB is attached, usb mounted means that the usb is readable by the system.
        usb_dict = {
            'usb_attached': self.has_usb_attached,
            'usb_mounted': not self.usb_button.button_state #originally this variable means "is_disabled?" so flip it to make sense to us
        }

        return usb_dict


    #This function uses a shared funtion in the Meta Reader Plugin to collect information from a pipe
    #without disturbing the main thread
    def collect_meta_data(self, dt):
        roboprinter.printer_instance.collect_data()
