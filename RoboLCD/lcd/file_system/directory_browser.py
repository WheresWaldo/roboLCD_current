# -*- coding: utf-8 -*-
# @Author: Matt Pedler
# @Date:   2017-09-27 17:53:43
# @Last Modified by:   Matt Pedler
# @Last Modified time: 2017-10-27 13:18:57


#kivy
from kivy.logger import Logger
from kivy.clock import Clock

#python
from functools import partial

#RoboLCD
from RoboLCD import roboprinter
from RoboLCD.lcd.Language import lang
class Directory_Browser(object):
    """
    docstring for Directory_Browser

    Directory Browser is meant to walk through the Octoprint directories and 
    save the current place in the directory. This way when a file edit happens we 
    can use the current directory from two different Directory_Browser objests 
    to get the original path and modify path.

    Directory Browser is also meant to walk through the directories and retrieve
    the current folders path 
    """

    current_directory = None
    root_directory = 'local'
    buttons=None
    def __init__(self):
        super(Directory_Browser, self).__init__()
        self.oprint = roboprinter.printer_instance
        self.buttons=None
        self.build_directory()
        

    def build_directory(self):
        self.directory = self.oprint._file_manager.list_files()['local']
        self.dir_name = lang.pack['Files']['Local']
        self.current_directory = File_Node(data=self.directory)

        #start a clock to analyze files
        # def analysis(dt):
        #     roboprinter.printer_instance.start_analysis(files=self.directory)
        # Clock.schedule_once(analysis, 0.2)
        

    def set_buttons(self, buttons):
        self.current_directory.buttons = buttons

    def return_file_data(self):
        return self.current_directory.file_data

    def return_current_directory(self):
        return self.current_directory.data

    def goto_root(self):
        while self.return_to_previous_directory():
            pass

    def return_to_previous_directory(self):
        if self.current_directory.prev_data != None:
            self.current_directory = self.current_directory.prev_data
            if self.current_directory.file_data != None:
                self.dir_name = self.current_directory.file_data['name']
            else:
                self.dir_name = lang.pack['Files']['Local']
            return True
        else:
            return False

    def goto_next_directory(self, name):

        if name in self.current_directory.data:
            if self.current_directory.data[name]['type'] == "folder":
                file_data = self.current_directory.data[name].copy()
                if 'children' in file_data:
                    del file_data["children"]
                #get next destinations files
                next_files = self.oprint._file_manager.list_files(path=file_data['path'])['local']
                self.current_directory = File_Node(data=next_files, prev_data=self.current_directory, file_data=file_data)
                self.dir_name = self.current_directory.file_data['name']
                return True
        #if it doesn't exist and it's not a folder then return false
        return False

    def refresh_cur_dir(self):
        #find current point in file system
        if self.current_directory.file_data != None and 'path' in self.current_directory.file_data:
            refreshed_files = self.oprint._file_manager.list_files(path=self.current_directory.file_data['path'])['local']
            # import json
            # Logger.info(json.dumps(refreshed_files, indent=4))

            #update current directory data
            self.current_directory.data = refreshed_files
            return True
        else:
            #Logger.info("No File data for this directory, refreshing to root directory")
            self.build_directory()
            return False

        

'''
File_Node is a linked list that will keep track of users path through data.
As a user moves through the data, there will be a generated list that will keep
track of previous directories and as the user backs out they can back through the 
linked list.
'''
class File_Node(object):
    data=None
    prev_data=None
    _buttons=None
    def __init__(self, data=None, prev_data=None, file_data=None, **kwargs):
        self.data=data
        self.prev_data=prev_data
        self.file_data=file_data

    def return_previous(self):
        return self.prev_data

    @property
    def buttons(self):
        #Logger.info("Getting Buttons for " + (self.file_data['name'] if self.file_data != None else "not named") + "!")
        #Logger.info("Returning: " + str(self._buttons))
        return self._buttons

    @buttons.setter
    def buttons(self, value):
        #Logger.info("Setting Buttons for " + (self.file_data['name'] if self.file_data != None else "not named") + "!")
        #Logger.info("Setting buttons to: " + str(value))
        self._buttons = value


'''
Screen node holds a linked list of screens to go backward to
'''
class Screen_Node(object):
    screen=None
    prev_screen = None
    def __init__(self, screen=None, prev_screen=None, **kwargs):
        self.screen = screen
        self.prev_screen = prev_screen

    def return_previous(self):
        return self.prev_screen

