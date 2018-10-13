# -*- coding: utf-8 -*-
# @Author: Matt Pedler
# @Date:   2017-09-27 17:53:43
# @Last Modified by:   Matt Pedler
# @Last Modified time: 2018-01-30 09:26:28
#kivy
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
from kivy.logger import Logger

#RoboLCD
from RoboLCD.lcd.pconsole import pconsole
from RoboLCD import roboprinter
from RoboLCD.lcd.Language import lang
from RoboLCD.lcd.scrollbox import Scroll_Box_Even, Scroll_Box_Even_Button
from RoboLCD.lcd.session_saver import session_saver
from RoboLCD.lcd.common_screens import KeyboardInput, Modal_Question_No_Title, Button_Group_Observer
from RoboLCD.lcd.connection_popup import Error_Popup, Warning_Popup
from directory_browser import Directory_Browser, Screen_Node
from file_screen import StandardFileButton, StandardFileView, File_Option_Button, File_Counter, File_Progress, Empty_Popup, KeyboardInput_file_bb



#python
from datetime import datetime
import os
import shutil
import traceback
from functools import partial

#octoprint
from octoprint.filemanager.storage import LocalFileStorage, StorageError

        
class FileOptions(Scroll_Box_Even):
    '''
    List Options will have a few different screens in it containing different lists of options.

    First List = Sort, Select Items to Edit, Create new Folder, Refresh

    These lists spawn different lists. instead of constantly switching out screens we are going
    to use one screen and update Scroll_Box_Even with a new list as needed.

    '''
    

    def __init__(self, show_files_callback, refresh_files, show_folders_callback, create_folder_callback, **kwargs):
        self.buttons = []
        super(FileOptions, self).__init__(self.buttons)
        self.waiting_for_input = False
        self.show_folders_callback = show_folders_callback
        self.settings = roboprinter.printer_instance._settings
        self.show_files_callback = show_files_callback
        self.refresh_files = refresh_files
        self.create_folder_callback = create_folder_callback
        self.original_screen = None
        self.sort_observer = Button_Group_Observer()
        self.modify_files_observer = Button_Group_Observer()

        #initialize this so that we can edit files on octoprint.
        base_folder = '/home/pi/.octoprint/uploads'
        self.storage = LocalFileStorage(base_folder)



        self.show_selectable_files_options = {
            'callback' : self.get_selected_files,
            'icon' : "Icons/Files_Icons/File_Options/Next.png"
        }

        self.button_dict = {
            'root_list':{'buttons':[
                            File_Option_Button(name=lang.pack['Files']['File_Options']['Sort_Files'],
                                               callback=partial(self.switch_lists, next_list='sort_files'),
                                               default_icon="Icons/Files_Icons/File_Options/Sort List.png"
                                               ),
                            File_Option_Button(name=lang.pack['Files']['File_Options']['Select_Items'],
                                               callback=partial(self.show_files_callback, callback_dict=self.show_selectable_files_options),
                                               default_icon="Icons/Files_Icons/File_Options/Select items.png"
                                               ),
                            File_Option_Button(name=lang.pack['Files']['File_Options']['Create_Folder'],
                                               callback=self.create_folder_callback,
                                               default_icon="Icons/Files_Icons/File_Options/Create new folder.png"
                                               ),
                            File_Option_Button(name=lang.pack['Files']['File_Options']['Refresh'],
                                               callback=self.refresh,
                                               default_icon="Icons/Files_Icons/File_Options/Refresh.png"
                                               )
            
                        ],
                        'title': lang.pack['Files']['File_Options']['Title'],
                        'option_function': self.exit_from_file_explorer,
                        'option_icon': "Icons/cancel_button_icon.png"
                        },

            'sort_files': {
                        'buttons':[
                            File_Option_Button(name=lang.pack['Files']['Sort_Files']['Alphabet'],
                                               default_icon="Icons/Files_Icons/File_Options/Alphabetically.png",
                                               observer=self.sort_observer, 
                                               selected=False,
                                               extra_content=True,
                                               option_list=[lang.pack['Files']['Sort_Files']['Alphabet_Options']['A2Z'], lang.pack['Files']['Sort_Files']['Alphabet_Options']['Z2A']]
                                               ),
                            File_Option_Button(name=lang.pack['Files']['Sort_Files']['Size'],
                                               observer=self.sort_observer, 
                                               default_icon="Icons/Files_Icons/File_Options/By size.png",
                                               selected=False,
                                               extra_content=True,
                                               option_list=[lang.pack['Files']['Sort_Files']['Size_Options']['L2S'], lang.pack['Files']['Sort_Files']['Size_Options']['S2L']]
                                               ),
                            File_Option_Button(name=lang.pack['Files']['Sort_Files']['Date'],
                                               observer=self.sort_observer, 
                                               default_icon="Icons/Files_Icons/File_Options/By date.png",
                                               selected=True,
                                               extra_content=True,
                                               option_list=[lang.pack['Files']['Sort_Files']['Date_Options']['New'], lang.pack['Files']['Sort_Files']['Date_Options']['Old']]
                                               ),
                            File_Option_Button(name=lang.pack['Files']['Sort_Files']['Type'],
                                               observer=self.sort_observer, 
                                               default_icon="Icons/Files_Icons/File_Options/By type.png",
                                               selected=False,
                                               extra_content=True,
                                               option_list=[lang.pack['Files']['Sort_Files']['Type_Options']['STL'], lang.pack['Files']['Sort_Files']['Type_Options']['GCODE'], lang.pack['Files']['Sort_Files']['Type_Options']['HEX'], lang.pack['Files']['Sort_Files']['Type_Options']['Folder']]
                                               )
                        ],
                        'title': lang.pack['Files']['Sort_Files']['Title'],
                        'option_function': self.set_sorting_options,
                        'option_icon': "Icons/Files_Icons/File_Options/Next.png"},

            'modify_files':{
                    'buttons':[
                            File_Option_Button(default_icon="Icons/Files_Icons/File_Options/Copy files.png",
                                               selected_icon="Icons/check_icon.png",
                                               name=lang.pack['Files']['Modify_Files']['Copy'],
                                               observer=self.modify_files_observer, 
                                               selected=False

                                               ),
                            File_Option_Button(default_icon="Icons/Files_Icons/File_Options/Move files.png",
                                               selected_icon="Icons/check_icon.png",
                                               name=lang.pack['Files']['Modify_Files']['Move'],
                                               observer=self.modify_files_observer, 
                                               selected=False
                                               
                                               ),
                            File_Option_Button(default_icon="Icons/Files_Icons/File_Options/Delete files.png",
                                               selected_icon="Icons/check_icon.png",
                                               name=lang.pack['Files']['Modify_Files']['Delete'],
                                               observer=self.modify_files_observer, 
                                               selected=False
                                               
                                               ),
                            File_Counter("0")
                        ],
                    'title': lang.pack['Files']['Modify_Files']['Title'],
                    'option_function': self.modify_files,
                    'option_icon': "Icons/Files_Icons/File_Options/Next.png"
            }

        }

        self.cur_list = Screen_Node(screen=self.button_dict['root_list'])
        self.populate_screen()
        self.set_default_sorting_option()

    def exit_from_file_explorer(self):
        

        #back function for cancel and the backbutton
        back_destination = roboprinter.screen_controls.get_screen_data()
        back_function = partial(roboprinter.screen_controls.populate_old_screen, screen=back_destination)

        def confirm_exit():
            body_text = lang.pack['Files']['File_Options']['Exit_File_Options']['Body']
            option1 = lang.pack['Files']['File_Options']['Exit_File_Options']['Option1']
            option2 = lang.pack['Files']['File_Options']['Exit_File_Options']['Option2']
            modal_screen = Modal_Question_No_Title(body_text, 
                                                   option1, 
                                                   option2, 
                                                   exit_fe, 
                                                   cancel_action
                                                   )

            #add to the screen
            roboprinter.screen_controls.set_screen_content(modal_screen,
                                                           lang.pack['Files']['File_Options']['Exit_File_Options']['Title'],
                                                           back_function=back_function,
                                                           option_function = 'no_option')

        def cancel_action():
            back_function()

        def exit_fe():
            roboprinter.robosm.go_back_to_main('printer_status_tab' )
        
        confirm_exit()

    def switch_lists(self, next_list):
        if next_list in self.button_dict:
            self.cur_list = Screen_Node(screen=self.button_dict[next_list], prev_screen=self.cur_list)
            self.populate_screen()
            return True
        return False

    def return_to_previous_list(self):
        if self.cur_list.prev_screen != None:
            self.cur_list = self.cur_list.prev_screen
            self.populate_screen()
            return True
        else:
            if self.original_screen != None:
                roboprinter.screen_controls.populate_old_screen(self.original_screen)
            return False 

    def refresh(self, *args, **kwargs):
        #refresh File Lists
        self.refresh_files()
        roboprinter.screen_controls.populate_old_screen(self.original_screen)

    def populate_screen(self):

        self.buttons = self.cur_list.screen['buttons']
        self.title = self.cur_list.screen['title']
        self.repopulate_for_new_screen()

        #remake the File_BB screen
        roboprinter.screen_controls.update_title(self.title)

        #change the option function as needed
        if 'option_function' in self.cur_list.screen:
            roboprinter.screen_controls.update_option_function(self.cur_list.screen['option_function'], self.cur_list.screen['option_icon'])

    #This function links to the sorting buttons to detirmine what the sorting order of files should be
    #it will store this as a dictionary with the sort type and the option that goes along with that sorting type.
    def set_sorting_options(self):

        #grab all of the button states

        for option in self.button_dict['sort_files']['buttons']:
            if option.selected:
                self.sorting_option = {
                    'sort': option.original_name,
                    'modify': option.option_list[option.list_pos]
                }
                break
        #save the sorting option to settings
        self.settings.set(['sorting_config'], self.sorting_option)
        self.settings.save()

        #Go back to the file screen.
        self.return_to_previous_list()
        if self.original_screen != None:
            roboprinter.screen_controls.populate_old_screen(self.original_screen)
            

    def set_default_sorting_option(self):
        #get the saved sorting option
        self.sorting_option = self.settings.get(['sorting_config'])

        #Protection for new machines that do not have this value initialized yet.
        robo_sorting_options = [lang.pack['Files']['Sort_Files']['Type'],
                                lang.pack['Files']['Sort_Files']['Size'],
                                lang.pack['Files']['Sort_Files']['Date'],
                                lang.pack['Files']['Sort_Files']['Alphabet']]
        if self.sorting_option == {} or not self.sorting_option['sort'] in robo_sorting_options:
            self.set_sorting_options()

        #set that button to active
        for button in self.button_dict['sort_files']['buttons']:
            if button.original_name == self.sorting_option['sort']:
                button.select(True)
                for x in range(0, len(button.option_list)):
                    if button.option_list[x] == self.sorting_option['modify']:
                        button.list_pos = x
                        break
                break


    def get_sorting_options(self):
        return self.sorting_option

    #this callback has the previous screen passed to it, so it can restore the File_options object then switch the 
    #layout of that screen.
    def get_selected_files(self, file_list, file_options_screen, resume_file_select, update_selected_folders):
        #Logger.info("Getting selected files")

        self.selected_files = []
        selected_folders_path = {}

        for file in file_list:
            if file['selected']:
                #Logger.info('File: ' + str(file['name']) + ' added to list')
                self.selected_files.append(file)
                if file['type'] == 'folder':
                    selected_folders_path[file['path']] = file['name']

        #if nothing is selected then do nothing
        if len(self.selected_files) == 0:
            #Logger.info("No Items Selected")
            ep = Error_Popup(lang.pack['Files']['Errors']['No_Items1']['Title'],
                             lang.pack['Files']['Errors']['No_Items1']['Body'],
                             )
            ep.show()
            return

        #return modify buttons to their original state
        #This is so the user can pick their option without interference from us
        for button in self.button_dict['modify_files']['buttons']:
            if hasattr(button, 'selected'):
                button.selected = False
                button.select(button.selected)
            elif hasattr(button, 'update_count'):
                button.update_count(str(len(self.selected_files)))
            else:
                raise AttributeError("Has neither selected or update count.")

        #Throw the selected list over to file_explorer so it can block out any 
        update_selected_folders(selected_folders_path)
        #change screen back to lead back to the file select screen
        file_select_screen = roboprinter.screen_controls.get_screen_data()

        roboprinter.screen_controls.populate_old_screen(file_options_screen)
        self.switch_lists('modify_files')

        def back_function():
            self.return_to_previous_list() #return to the List Option Page
            resume_file_select() #tell the File Explorer to go back to the file select screen
            roboprinter.screen_controls.populate_old_screen(file_select_screen, ignore_update=True) #return to the file select screen

        roboprinter.screen_controls.update_back_function(back_function)


    def modify_files(self):
        #Logger.info("Modify the files!")

        for button in self.button_dict['modify_files']['buttons']:
            if hasattr(button, 'selected'):
                if button.selected:
                    self.execute_modification(button.original_name)
                    return

        #Logger.info("No Items Selected")
        ep = Error_Popup(lang.pack['Files']['Errors']['No_Items2']['Title'],
                         lang.pack['Files']['Errors']['No_Items2']['Body'],
                         )
        ep.show()
        #The code will only reach here if we did not find a selected button
        #Logger.info("No Option Selected!")

    def execute_modification(self, modify_option):
        
        self.modify_progress = File_Progress()
        self.modify_progress.update_title("[size=40]" + modify_option)

        #make the popup
        self.prog_popup = Empty_Popup(self.modify_progress)
        

        if modify_option == lang.pack['Files']['Modify_Files']['Delete']:

            #back function for cancel and the backbutton
            back_destination = roboprinter.screen_controls.get_screen_data()
            back_function = partial(roboprinter.screen_controls.populate_old_screen, screen=back_destination)

            def confirm_delete():
                body_text = lang.pack['Files']['Delete_File_Conf']['Body']
                option1 = lang.pack['Files']['Delete_File_Conf']['positive']
                option2 = lang.pack['Files']['Delete_File_Conf']['negative']
                modal_screen = Modal_Question_No_Title(body_text, 
                                                       option1, 
                                                       option2, 
                                                       delete_action, 
                                                       cancel_action
                                                       )

                #add to the screen
                roboprinter.screen_controls.set_screen_content(modal_screen,
                                                               lang.pack['Files']['Delete_File_Conf']['Title'],
                                                               back_function=back_function,
                                                               option_function = 'no_option')

            def cancel_action():
                back_function()

            def delete_action():
                self.delete_files()
                while(self.return_to_previous_list()):
                    pass

            confirm_delete()

        elif modify_option == lang.pack['Files']['Modify_Files']['Move']:
            #Logger.info("Moving files")
            self.MODE='MOVE'
            show_selectable_folders_options = {
                'callback' : self.get_directory,
                'icon' : "Icons/Files_Icons/File_Options/Next.png"
            }
            self.show_folders_callback(show_selectable_folders_options)
        elif modify_option == lang.pack['Files']['Modify_Files']['Copy']:
            #Logger.info("Copying files")
            self.MODE = 'COPY'
            show_selectable_folders_options = {
                'callback' : self.get_directory,
                'icon' : "Icons/Files_Icons/File_Options/Next.png"
            }
            self.show_folders_callback(show_selectable_folders_options)

    def get_directory(self, directory, file_explorer_callback):

        #Logger.info("Moving selected files to directory " + str(directory))

        if self.MODE == 'MOVE':
            self.move_files(directory, file_explorer_callback)
        elif self.MODE == 'COPY':
            self.copy_files(directory, file_explorer_callback)
        else:
            raise Exception("self.MODE is not set")


    #This function takes in filename and destination and outputs a filename with a _#.extension 
    def name_iterator(self, filename, destination, file_type = "folder"):
        #get the name and extension
        name, extension = os.path.splitext(filename)
        final_name = destination + "/" + name + extension #gotta check if the basename is available
        file_exists = True #initialize the value

        #different function based on filetype
        if file_type == "folder":
            file_exists = self.storage.folder_exists(final_name)
        else:
            file_exists = self.storage.file_exists(final_name)

        #if file doesn't exist then it will just return the basename
        counter = 0
        while file_exists:
            counter += 1
            final_name = destination + "/" + name + "_" + str(counter) + extension
            if file_type == "folder":
                file_exists = self.storage.folder_exists(final_name)
            else:
                file_exists = self.storage.file_exists(final_name)

        return final_name

    #This function is used for testing if two paths are the same file
    def same_file(self, filepath, name, destination):
        Logger.info(filepath)
        Logger.info(name)
        Logger.info(destination)
        if destination == '':
            final_destination = name
        else:
            final_destination = destination + "/" + name
        Logger.info(final_destination)
        if filepath == final_destination:
          return True
        return False


        
    '''
    Earlier in the class the user selects the files that he wants to modify, then chooses the type of modification(Copy). 
    Then the user selects the destination and then copy_files recieves a destination folder and a callback to call when it's 
    done modifying the files. Copy_Files then iterates over a list of files, if the file exists at the destination folder 
    already the User gets notified and asked to choose to either Replace, Keep Both Files, Or just skip the file. Then the 
    Correct action takes place and the function moves onto the next file. Rinse Repeat, then call the callback when finished
    '''
    def copy_files(self, destination, callback):

        #display Popup
        self.prog_popup.show()
        self.counter = 0 #progress
        self.max_count = len(self.selected_files)
        self.error_popup = False

        def skip():
            self.counter += 1
            prog = float(float(self.counter) / float(self.max_count) * 100.00) #percent progress
            self.modify_progress.update_progress(prog)
            self.modify_progress.file_exists = "[size=30]"+ lang.pack['Files']['Modify_Files']['Progress'] + str(self.counter) + " / " + str(self.max_count) + lang.pack['Files']['Modify_Files']['Files']
            #Logger.info( str(self.counter) + " " + str(self.max_count) + " " + str(prog))
            self.waiting_for_input = False
            self.modify_progress.button_state = True
            Clock.schedule_once(copy_next_file, 0.2) #loop

        def replace():
            self.modify_progress.button_state = True
            self.modify_progress.file_exists = "[size=30]"+ lang.pack['Files']['Modify_Files']['Progress'] + str(self.counter) + " / " + str(self.max_count) + lang.pack['Files']['Modify_Files']['Files']

            def replace_action(dt):
                try:
                    #check to see if the file is the same file we are about to delete
                    source_abs_path = self.storage.path_on_disk(self.file['path'])
                    dest_abs_path = self.storage.path_on_disk(destination + "/" + self.file['name'])
                    if os.path.samefile(source_abs_path, dest_abs_path):
                        #Logger.info("File and destination are the same, Not doing anything\n" + str(source_abs_path) + "\n" + str(dest_abs_path))
                        pass
                    else:
                        
                            if self.file['type'] == "folder":
                                #Logger.info("Removing File")
                                self.storage.remove_folder(destination + "/" + self.file['name'], recursive=True)
                                #Logger.info("Copying File")
                                self.storage.copy_folder(self.file['path'], destination + "/" + self.file['name'])
                            else:
                                #Logger.info("Removing File")
                                self.storage.remove_file(destination + "/" + self.file['name'])
                                #Logger.info("Copying File")
                                self.storage.copy_file(self.file['path'], destination + "/" + self.file['name'])

                except Exception as e:
                    Logger.info("!!!!!!!!!!!!!!! Error: " + str(e))
                    traceback.print_exc()
                    error_out() 
                finally:                  
                    skip()

            #schedule the replace action so the screen can update accordingly
            Clock.schedule_once(replace_action, 0.2)

        def keep_both():
            self.modify_progress.button_state = True
            self.modify_progress.file_exists = "[size=30]"+ lang.pack['Files']['Modify_Files']['Progress'] + str(self.counter) + " / " + str(self.max_count) + lang.pack['Files']['Modify_Files']['Files']
            #check if the file exists or not and ask user what they want to do
            def keep_action(dt):
                try:
                    if self.file['type'] == "folder":
                        final_name = self.name_iterator(self.file['name'], destination, file_type='folder')
                        self.storage.copy_folder(self.file['path'], final_name)
        
                    else:
                        final_name = self.name_iterator(self.file['name'], destination, file_type='file')
                        self.storage.copy_file(self.file['path'], final_name)
                except Exception as e:
                    Logger.info("!!!!!!!!!!!!!!! Error: " + str(e))
                    traceback.print_exc()
                    error_out() 
                finally:    
                    skip()

            Clock.schedule_once(keep_action, 0.2)
        

        def file_exists():
            self.modify_progress.file_exists = "[size=30][color=FF0000]" + lang.pack['Files']['Modify_Files']['File_Exists']
            self.modify_progress.replace = replace
            self.modify_progress.keep_both = keep_both
            self.modify_progress.skip = skip
            self.modify_progress.button_state = False
            self.waiting_for_input = True

        def error_out():
            if not self.error_popup:
                self.error_popup = True
                ep = Error_Popup(lang.pack['Files']['File_Options']['Copy_Error']['Title'], lang.pack['Files']['File_Options']['Copy_Error']['Body'])
                ep.show() 
            self.counter = self.max_count - 1  

        #Copy next ticker. This gets called until all files have been copied. It updates the progress bar.
        def copy_next_file(*args, **kwargs):
            try:
                if self.counter < self.max_count:
                    file = self.selected_files[self.counter]
                    self.file = file
                    #Logger.info("Copying: " + str(file['name']) + " " + str(file['path']) + " to " + destination)
                    self.modify_progress.update_file(str(file['name']))
                    #check if the file exists or not and ask user what they want to do
                    if file['type'] == "folder":
                        if not self.storage.folder_exists(destination + "/" + file['name']):
                            self.storage.copy_folder(file['path'], destination + "/" + file['name'])
                        else:
                            file_exists()
        
                    else:
                        if not self.storage.file_exists(destination + "/" + file['name']):
                            self.storage.copy_file(file['path'], destination + "/" + file['name'])
                        else:
                            file_exists()      
            except Exception as e:
                Logger.info("!!!!!!!!!!!!!!! Error: " + str(e))
                traceback.print_exc()
                error_out()  
            

            #check if it's finished
            if self.counter == self.max_count:
                self.prog_popup.hide()
                #return file options to root options
                while self.return_to_previous_list():
                    pass
                callback()
                return False
            else:
                if not self.waiting_for_input:
                    skip()



        Clock.schedule_once(copy_next_file, 0.2)
       
    '''
    move_files does the same thing as copy_files, but it actually moves the original file. I know we are supposed to use the DRY method, but Copy files is 
    all over the place and adding in another clause for checking the mode seemed to make the source code even more confusing than it already is. So I opted to 
    just repeat copy files except change copy_folder/file to move_folder/file
    '''
    
    def move_files(self, destination, callback):

        #display Popup
        self.prog_popup.show()
        self.counter = 0 #progress
        self.max_count = len(self.selected_files)
        self.error_popup = False

        def skip():
            self.counter += 1
            prog = float(float(self.counter) / float(self.max_count) * 100.00) #percent progress
            self.modify_progress.update_progress(prog)
            self.modify_progress.file_exists = "[size=30]"+ lang.pack['Files']['Modify_Files']['Progress'] + str(self.counter) + " / " + str(self.max_count) + lang.pack['Files']['Modify_Files']['Files']
            #Logger.info( str(self.counter) + " " + str(self.max_count) + " " + str(prog))
            self.waiting_for_input = False
            self.modify_progress.button_state = True
            Clock.schedule_once(move_next_file, 0.2) #loop

        def replace():
            self.modify_progress.button_state = True
            self.modify_progress.file_exists = "[size=30]"+ lang.pack['Files']['Modify_Files']['Progress'] + str(self.counter) + " / " + str(self.max_count) + lang.pack['Files']['Modify_Files']['Files']

            def replace_action(dt):
                try:
                    #check to see if the file is the same file we are about to delete
                    source_abs_path = self.storage.path_on_disk(self.file['path'])
                    dest_abs_path = self.storage.path_on_disk(destination + "/" + self.file['name'])
                    if os.path.samefile(source_abs_path, dest_abs_path):
                        #Logger.info("File and destination are the same, Not doing anything\n" + str(source_abs_path) + "\n" + str(dest_abs_path))
                        pass
                    else:
                        if self.file['type'] == "folder":
                            #Logger.info("Removing File")
                            self.storage.remove_folder(destination + "/" + self.file['name'], recursive=True)
                            #Logger.info("Moving File")
                            self.storage.move_folder(self.file['path'], destination + "/" + self.file['name'])
                        else:
                            #Logger.info("Removing File")
                            self.storage.remove_file(destination + "/" + self.file['name'])
                            #Logger.info("Moving File")
                            self.storage.move_file(self.file['path'], destination + "/" + self.file['name'])
                except Exception as e:
                    Logger.info("!!!!!!!!!!!!!!! Error: " + str(e))
                    traceback.print_exc()
                    error_out() 
                finally:    
                    skip()

            #schedule the replace action so the screen can update accordingly
            Clock.schedule_once(replace_action, 0.2)

        def keep_both():
            self.modify_progress.button_state = True
            self.modify_progress.file_exists = "[size=30]"+ lang.pack['Files']['Modify_Files']['Progress'] + str(self.counter) + " / " + str(self.max_count) + lang.pack['Files']['Modify_Files']['Files']
            #check if the file exists or not and ask user what they want to do
            def keep_action(dt):
                try:
                    if self.file['type'] == "folder":
                        same_folder = self.same_file(self.file['path'], self.file['name'], destination)
                        final_name = self.name_iterator(self.file['name'], destination, file_type='folder')

                        if not same_folder:
                          self.storage.move_folder(self.file['path'], final_name)
                        else:
                          self.storage.copy_folder(self.file['path'], final_name)
        
                    else:
                        same_file = self.same_file(self.file['path'], self.file['name'], destination)
                        final_name = self.name_iterator(self.file['name'], destination, file_type='file')

                        if not same_file:
                          self.storage.move_file(self.file['path'], final_name)
                        else:
                          self.storage.copy_file(self.file['path'], final_name)

                except Exception as e:
                    Logger.info("!!!!!!!!!!!!!!! Error: " + str(e))
                    traceback.print_exc()
                    error_out() 
                finally:    
                    skip()

            Clock.schedule_once(keep_action, 0.2)
        

        def file_exists():
            self.modify_progress.file_exists = "[size=30][color=FF0000]" + lang.pack['Files']['Modify_Files']['File_Exists']
            self.modify_progress.replace = replace
            self.modify_progress.keep_both = keep_both
            self.modify_progress.skip = skip
            self.modify_progress.button_state = False
            self.waiting_for_input = True

        def error_out():
            if not self.error_popup:
                self.error_popup = True
                ep = Error_Popup(lang.pack['Files']['File_Options']['Move_Error']['Title'], lang.pack['Files']['File_Options']['Move_Error']['Body'])
                ep.show() 
            self.counter = self.max_count - 1   

        #Copy next ticker. This gets called until all files have been copied. It updates the progress bar.
        def move_next_file(*args, **kwargs):
            try:
                if self.counter < self.max_count:
                    file = self.selected_files[self.counter]
                    self.file = file
                    #Logger.info("Moving: " + str(file['name']) + " " + str(file['path']) + " to " + destination)
                    self.modify_progress.update_file(str(file['name']))
                    #check if the file exists or not and ask user what they want to do
                    if file['type'] == "folder":
                        if not self.storage.folder_exists(destination + "/" + file['name']):
                            self.storage.move_folder(file['path'], destination + "/" + file['name'])
                        else:
                            file_exists()
        
                    else:
                        if not self.storage.file_exists(destination + "/" + file['name']):
                            self.storage.move_file(file['path'], destination + "/" + file['name'])
                        else:
                            file_exists()          
            except Exception as e:
                Logger.info("!!!!!!!!!!!!!!! Error: " + str(e))
                traceback.print_exc()
                error_out() 
               

            #check if it's finished
            if self.counter == self.max_count:
                self.prog_popup.hide()
                #return file options to root options
                while self.return_to_previous_list():
                    pass
                callback()
                return False
            else:
                if not self.waiting_for_input:
                    skip()



        Clock.schedule_once(move_next_file, 0.2)
        


    '''
    delete_files will delete all selected files and show the progress to the screen.
    '''
    def delete_files(self):
        #display Popup
        self.prog_popup.show()
        self.counter = 0 #progress
        self.max_count = len(self.selected_files)
        self.error_popup = False

        def error_out():
            if not self.error_popup:
                self.error_popup = True
                ep = Error_Popup(lang.pack['Files']['File_Options']['Delete_Error']['Title'], lang.pack['Files']['File_Options']['Delete_Error']['Body'])
                ep.show()
            self.counter = self.max_count - 1   

        def skip():
            self.counter += 1
            prog = float(float(self.counter) / float(self.max_count) * 100.00) #percent progress
            self.modify_progress.update_progress(prog)
            self.modify_progress.file_exists = "[size=30]"+ lang.pack['Files']['Modify_Files']['Progress'] + str(self.counter) + " / " + str(self.max_count) + lang.pack['Files']['Modify_Files']['Files']
            #Logger.info( str(self.counter) + " " + str(self.max_count) + " " + str(prog))
            self.waiting_for_input = False
            self.modify_progress.button_state = True
            Clock.schedule_once(delete_next_file, 0.2) #loop


        #delete ticker, this will delete all files until there are no more left
        def delete_next_file(*args, **kwargs):
            try:
                if self.counter < self.max_count:
                    file = self.selected_files[self.counter]
                    self.file = file
                    #Logger.info("Deleting: " + str(file['name']) + " " + str(file['path']))
                    self.modify_progress.update_file(str(file['name']))
                    #delete the files
                    if file['type'] == "folder":
                        self.storage.remove_folder(file['path'], recursive=True)
                    else:
                        self.storage.remove_file(file['path'])
            except:
                Logger.info("!!!!!!!!!!!!!!! Error: " + str(e))
                traceback.print_exc()
                error_out() 

            #check if it's finished
            if self.counter == self.max_count:
                self.prog_popup.hide()
                #return file options to root options
                while self.return_to_previous_list():
                    pass
                return False
            else:
                if not self.waiting_for_input:
                    skip()



        Clock.schedule_once(delete_next_file, 0.2)

    #This will change the permissions to the USB folder and try again. This
    # def change_permissions_and_try_create_folder(self, destination):
    #     try:
    #         import os
    #         import subprocess
    #         #chown the USB folder
    #         USB_folder =  os.path.expanduser('~/.octoprint/uploads/USB')
    #         command = "sudo chown pi:pi " + str(USB_folder)
    #         Logger.info("Executing command " + str(command))
    
    #         #wait for command to finish executing
    #         subprocess.Popen(command,
    #                          stdout=subprocess.PIPE,
    #                          shell=True
    #                          )
    #         output, error = temp_p.communicate()
    #         p_status = temp_p.wait()

    #         Logger.info("Finished Executing! Attempting to add folder!")
    
    #         self.storage.add_folder(destination, ignore_existing=True)
    #         return True
    #     except Exception as e:
    #         Logger.info("Creating Permissions Failed! Erroring out!")
    #         return False

    def create_new_folder(self, destination, file_callback):

        #get the current screen so we can travel back to it
        current_screen = roboprinter.screen_controls.get_screen_data()
        back_function = partial(roboprinter.screen_controls.populate_old_screen, screen=current_screen)
        self.error_popup = False

        def error_out():
            if not self.error_popup:
                self.error_popup = True
                ep = Error_Popup(lang.pack['Files']['File_Options']['Folder_Error']['Title'], lang.pack['Files']['File_Options']['Folder_Error']['Body'])
                ep.show()

        def create_keyboard(default_text = lang.pack['Files']['Keyboard']['New_Folder']):
            #populate a screen with a keyboard as the object
            KeyboardInput_file_bb(keyboard_callback = get_keyboard_data,
                                  back_destination=current_screen,
                                  default_text = default_text)

        def get_keyboard_data(folder_name):

            def rename():
                create_keyboard(default_text=folder_name)


            def make_new_folder_action():
                try:
                    self.storage.add_folder(destination + '/' + folder_name, ignore_existing=True)
                except Exception as e:
                    Logger.info("!!!!!!!!!!!!!!!!!!!!! Error!")
                    traceback.print_exc()
                    error_out()


                
    
                #return file options to root options
                while self.return_to_previous_list():
                    pass
    
                #go back to file explorer
                file_callback()

            if self.storage.folder_exists(destination + '/' + folder_name):

                title = lang.pack['Files']['Keyboard']['Error']['Title']
                body_text= lang.pack['Files']['Keyboard']['Error']['Body']
                option1 = lang.pack['Files']['Keyboard']['Error']['Rename']
                option2 = lang.pack['Files']['Keyboard']['Error']['Cancel']
                modal_screen = Modal_Question_No_Title(body_text,
                                                       option1,
                                                       option2,
                                                       rename,
                                                       back_function
                                                       )

                #make screen
                roboprinter.screen_controls.set_screen_content(modal_screen,
                                                               title,
                                                               back_function = back_function,
                                                               option_function = 'no_option')
            else:
                make_new_folder_action()

        create_keyboard()

        
        
        


    

