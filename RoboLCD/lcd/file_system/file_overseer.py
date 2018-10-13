# -*- coding: utf-8 -*-
# @Author: Matt Pedler
# @Date:   2017-09-27 17:53:43
# @Last Modified by:   Matt Pedler
# @Last Modified time: 2017-10-27 13:19:38
from file_back_button import File_BB
from file_explorer import File_Explorer
from file_options import FileOptions 

from RoboLCD import roboprinter

from kivy.logger import Logger
from functools import partial


class File_Overseer(object):
    """
    docstring for File_Overseer
    
    File Overseer will stitch all of the different parts together.
    """
    switcher = True
    def __init__(self):
        super(File_Overseer, self).__init__()
        #self.make_screen()
        self.bb_screen = File_BB()
        self.exit =  False
        roboprinter.screen_controls = self.bb_screen

        pass

    def make_screen(self):
        self.file_options = FileOptions(self.show_selectable_files, self.refresh, self.folders_only, self.create_folder)
        self.file_explorer = File_Explorer(self.file_options.storage,  self.folders_only)
        self.goto_file_explorer()

        return self.bb_screen

    def goto_USB(self):
      self.file_explorer.directory.goto_root()
      self.file_explorer.next_directory('USB')
      self.file_explorer.set_exit()
      self.exit = True
      self.goto_file_explorer()

    def goto_root(self):
      self.exit = False
      self.file_explorer.directory.goto_root()
      self.goto_file_explorer()
      
      

    def goto_file_options(self):
        self.file_options.original_screen = roboprinter.screen_controls.get_screen_data()
        roboprinter.screen_controls.set_screen_content(self.file_options, #content
                                                       self.file_options.title, #title of content
                                                       back_function=self.file_options.return_to_previous_list, #back button function
                                                       option_function=self.file_options.exit_from_file_explorer,
                                                       option_icon="Icons/cancel_button_icon.png") #option Button function

    def goto_file_explorer(self):
        self.file_explorer.update_file_screen()
        back_function = partial(self.file_explorer.up_one_directory, exit=self.exit)
        roboprinter.screen_controls.set_screen_content(self.file_explorer, #content
                                                       self.file_explorer.current_title, #title of content
                                                       back_function=back_function, #back button function
                                                       option_function=self.goto_file_options,
                                                       option_icon="Icons/Files_Icons/Hamburger_lines.png") #option Button function
    

    def show_selectable_files(self, callback_dict):
        previous_screen = roboprinter.screen_controls.get_screen_data()
        def option_button_function():
            callback_dict['callback'](self.file_explorer.file_list, previous_screen, self.file_explorer.resume_selectable_dir, self.file_explorer.update_selected_folders)

        self.file_explorer.show_selectable_cur_dir()
        
        back_function = partial(self.back_to_previous, screen=previous_screen)
        icon = callback_dict['icon']

        roboprinter.screen_controls.set_screen_content(self.file_explorer, #content
                                                       self.file_explorer.current_title, #title of content
                                                       back_function=back_function, #back button function
                                                       option_function=option_button_function, #option Button function
                                                       option_icon=icon)

    def back_to_previous(self, screen):
        # Logger.info("Returning to previous screen")
        roboprinter.screen_controls.populate_old_screen(screen)

    def refresh(self):
        self.file_explorer.refresh()

    def folders_only(self, callback_dict, back_to_name=None):
        #get the previous screen
        previous_screen = roboprinter.screen_controls.get_screen_data()
        #make a partial that will recall the previous screen
        back_function = partial(self.back_to_previous, screen=previous_screen)
        #make a partial that will give that callback to the back_button as well as a screen name and let the backbutton decide where to go
        folder_only_back = partial(self.file_explorer.folders_only_back_button, previous_screen_callback=back_function, back_to_name=back_to_name)

        def option_button_function():
            callback_dict['callback'](self.file_explorer.return_current_directory(), self.goto_file_explorer)

        
        self.file_explorer.show_only_folders()
        
        icon = callback_dict['icon']

        roboprinter.screen_controls.set_screen_content(self.file_explorer, #content
                                                       self.file_explorer.current_title, #title of content
                                                       back_function=folder_only_back, #back button function
                                                       option_function=option_button_function, #option Button function
                                                       option_icon=icon)

    '''
    This gets executed by file options when a new folder needs to be created.
    '''
    def create_folder(self):
      #get current directory
      cur_dir = self.file_explorer.return_current_directory()
      self.file_options.create_new_folder(cur_dir, self.goto_file_explorer)
