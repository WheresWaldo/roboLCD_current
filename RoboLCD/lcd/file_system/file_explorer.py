# -*- coding: utf-8 -*-
# @Author: Matt Pedler
# @Date:   2017-09-27 17:53:43
# @Last Modified by:   Matt Pedler
# @Last Modified time: 2017-12-06 16:40:49

#kivy
from kivy.logger import Logger

#RoboLCD
from RoboLCD import roboprinter
from RoboLCD.lcd.Language import lang
from RoboLCD.lcd.session_saver import session_saver
from RoboLCD.lcd.common_screens import KeyboardInput, Modal_Question_No_Title, Button_Group_Observer
from RoboLCD.lcd.connection_popup import Error_Popup
from directory_browser import Directory_Browser
from file_screen import StandardFileButton, StandardFileView, FolderButton, File_Option_Button, Scroll_Box_File_List, PrintFile
from RoboLCD.lcd.slicer_wizard import Slicer_Wizard

#python
from datetime import datetime
import os
import shutil
import traceback
from functools import partial
import copy

#octoprint
import time


#File explorer and directory browser use each other to navigate through the filesystem. File Explorer will use the information from Directory_Browser and
#display the current file system. File Explorer will just maintain the list and the graphical interface to all files.
USB_DIR = '/home/pi/.octoprint/uploads/USB'
FILES_DIR = '/home/pi/.octoprint/uploads'
class File_Explorer(Scroll_Box_File_List):
    
    def __init__(self, storage_manager, show_only_folders_callback, **kwargs):

        #default title
        self.current_title = lang.pack['Files']['Local']
        self.settings = roboprinter.printer_instance._settings
        self.editing = False
        self.directory = Directory_Browser()
        self.oprint = roboprinter.printer_instance
        self.file_list = []
        self.show_only_folders_callback = show_only_folders_callback
        self.selected_folders = {}
        #initialize scroll box even

        self.storage = storage_manager
        super(File_Explorer, self).__init__(self.file_list, self.file_callback)

        self.update_file_screen()

    def file_callback(self, file_data, **kwargs):
        if file_data['type'] == 'folder':
            self.next_directory(file_data['name'])
        else:
            self.add_view_to_screen(file_data)

    def refresh(self):
        #self.directory.refresh_nodes()
        self.directory.refresh_cur_dir()
        #Logger.info("Refreshing Files")
        self.update_file_screen()

    def timing(function):
        def timer_wrap(*args, **kwargs):
            time1 = time.time()
            returned = function(*args, **kwargs)
            time2 = time.time()
            Logger.info(function.func_name + " took " + str((time2-time1)*1000.0) + "ms to execute")
            return returned
        return timer_wrap

    def return_current_directory(self):
        if self.directory.return_file_data() != None:
            return self.directory.return_file_data()['path']
        else:
            return '' #root directory

    #@timing 
    def update_file_screen(self):
        #time this transaction
        self.editing = False
        self.directory.refresh_cur_dir()
        self.files = self.directory.return_current_directory()
        self.update_callback(self.file_callback)
        self.current_title = self.directory.dir_name
        roboprinter.screen_controls.update_title(self.current_title)
        self.update_screen_list()

        

    def update_screen_list(self):
        gcode_buttons = []
        firmware_buttons = []
        stl_buttons = []
        folders = []
        #sort files into types
        for entry in self.files:
            if self.files[entry]['type'] == "firmware":
                #create a button for firmware
                firmware_buttons.append(self.files[entry])
                
            elif self.files[entry]['type'] == "machinecode":
                #create a button for gcode
                gcode_buttons.append(self.files[entry])
            elif self.files[entry]['type'] == "model":
                #create a button for stl
                stl_buttons.append(self.files[entry])
            elif self.files[entry]['type'] == 'folder':
                if entry != 'USB' and entry.find('System_Volume_Information') == -1:
                    folders.append(self.files[entry])

                #only add the USB file if it is mounted and we aren't trying to edit the filesystem
                elif entry == 'USB' and session_saver.saved['usb_mounted'] == True and not self.editing:
                    folders.append(self.files[entry])


        self.file_list = self.order_buttons(gcode_buttons, stl_buttons, firmware_buttons, folders)
        self.repopulate_for_new_screen()

    #@timing
    def show_selectable_cur_dir(self, resume=False):

        #we don't want the user to be able to delete the USB file. set this flag to true
        self.editing = True
        #add in the selected option to each file in the directory
        if not resume:
            for x in range(0, len(self.file_list)):
                #add key 'selected'
                self.file_list[x]['selected'] = False

            #copy where we are at
            self.resume_directory = self.directory.current_directory.file_data
            
        else:
            self.file_list = self.resume_files_list

        self.update_callback(self.select_file)
        

        #update title
        self.current_title = self.directory.dir_name
        roboprinter.screen_controls.update_title(self.current_title)

        if not resume:
            self.update_screen_list()
            self.resume_files_list = list(self.file_list)
        else:
            self.repopulate_for_new_screen()

    def select_file(self, file_data):
        for x in range(0, len(self.file_list)):
            if self.file_list[x]['name'] == file_data['name']:
                self.file_list[x]['selected'] = not self.file_list[x]['selected'] #toggle 
                self.update_button_status()
                break

    def resume_selectable_dir(self):
        self.show_selectable_cur_dir(resume=True)

    def update_selected_folders(self, selected_folders):
        self.selected_folders = selected_folders

    #@timing
    def show_only_folders(self):
        
        #we aren't editing the filesystem anymore so going to the USB is okay again
        self.editing = False
        #copy where we are at
        self.resume_directory = self.directory.current_directory.file_data
        #return to root directory
        while self.directory.return_to_previous_directory():
            pass
        folders_only = {}
        self.files = self.directory.return_current_directory()

        for file in self.files:
            if self.files[file]['type'] == 'folder' and self.files[file]['path'] not in self.selected_folders:
                new_entry = {file:self.files[file]}
                folders_only.update(new_entry)

        self.files = folders_only
        self.update_callback(self.folders_only_callback)
        self.current_title = self.directory.dir_name
        roboprinter.screen_controls.update_title(self.current_title)
        self.update_screen_list()

    def folders_only_callback(self, file_data):
        if self.directory.goto_next_directory(file_data['name']):

            self.current_title = file_data['name']
            folders_only = {}
            self.update_folders()
            roboprinter.screen_controls.update_title(self.current_title)
        else:
            Logger.info("Not and Option! " + str(name))

    def folders_only_back_button(self, previous_screen_callback, back_to_name=None):
        if self.directory.return_to_previous_directory():
            self.current_title = self.directory.dir_name
            self.update_folders()

            roboprinter.screen_controls.update_title(self.current_title)
        else:
            Logger.info("Cant go back any farther! Returning to previous screen.")
            self.return_to_previous_file_pos() #returns file explorer to the directory it left off at

            #go back to previous screen
            previous_screen_callback()
            if back_to_name != None:
                roboprinter.robosm.current = back_to_name

    def return_to_previous_file_pos(self):
        #go back to root
        while self.directory.return_to_previous_directory():
            pass

        #grab the current directories files since Show only folders makes the files have only folders
        self.files = self.directory.return_current_directory()


        #walk to the resumed dir
        if self.resume_directory != None and 'path' in self.resume_directory:
            if self.resume_directory['path'].find('/') != -1:
                directory = self.resume_directory['path'].split('/')
                for path in directory:
                    self.next_directory(path)
            else:
                self.next_directory(self.resume_directory['path'])

    def update_folders(self):
        self.files = self.directory.return_current_directory()
        folders_only = {}

        for file in self.files:
            if self.files[file]['type'] == 'folder' and self.files[file]['path'] not in self.selected_folders:
                new_entry = {file:self.files[file]}
                folders_only.update(new_entry)

        self.files = folders_only.copy()

        self.update_screen_list()
    
    #callback for updating the screen with a new sort order
    def update(self):
        self.update_file_screen()



        
    def add_view_to_screen(self, file_data):

        def firmware_wizard(file_data, *args, **kwargs):
            path = self.storage.path_on_disk(file_data['path'])
            roboprinter.printer_instance.flash_usb(path)
        #figure out what type of file we have 

        #execute the Firmware Wizard!
        if file_data['type'] == "firmware":
            back_screen = roboprinter.screen_controls.get_screen_data()
            back_button = partial(roboprinter.screen_controls.populate_old_screen, screen=back_screen)
            layout = StandardFileView(file_data, roboprinter.lang.pack['Firmware_Wizard']['Start_Firmware'] ,firmware_wizard)
            roboprinter.screen_controls.set_screen_content(layout, roboprinter.lang.pack['Firmware_Wizard']['Title'], 
                                                           back_function=back_button, 
                                                           option_function = 'no_option')
        
        #Make a File Screen and Print
        elif file_data['type'] == "machinecode":
            layout = PrintFile(file_data)
            back_screen = roboprinter.screen_controls.get_screen_data()
            back_button = partial(roboprinter.screen_controls.populate_old_screen, screen=back_screen)
            back_function = partial(layout.exit_function, exit_callback=back_button)
            roboprinter.screen_controls.set_screen_content(layout, 
                                                           file_data['name'], 
                                                           back_function=back_function,
                                                           option_function = 'no_option')

        #Start the Slicer Wizard
        elif file_data['type'] == "model":
            Slicer_Wizard(file_data, self.slicer_wizard_callback)

    def slicer_wizard_callback(self, temp_file_path, file_meta_data, back_to_name=None):

        def save_meta_data():
            if os.path.isfile(temp_file_path):
                with open(temp_file_path, "a") as file:
                    file.write("\n\n") #skip two lines
                    file.write("; Custom Meta Data from RoboLCD Written by Matt Pedler:\n")
                    for meta in file_meta_data:
                        file.write("; " + str(meta) + " = " + str(file_meta_data[meta]) + "\n")
            else:
                Logger.info("Failed to write Meta Data to file " + str(temp_file_path))
    
        #use this function to save
        def save_to_dir(directory, goto_file_explorer_callback):
            #save the meta data first
            save_meta_data()

            #save the file to the directory
            filename = os.path.basename(temp_file_path)

            save_directory = self.storage.path_on_disk(directory)

            Logger.info("Saving " + filename + " to " + save_directory)

            final_directory = save_directory + '/' + filename
            copy_final = final_directory

            counter = 0
            #don't overwrite an already saved file
            while os.path.isfile(final_directory):
                counter += 1
                final_directory = copy_final.replace(".gcode", "_" + str(counter) + ".gcode")

            #actually save the file
            if os.path.isfile(temp_file_path):
                shutil.copyfile(temp_file_path, final_directory)
                os.remove(temp_file_path)
            else:
                Logger.info("Temp file no longer exists!!!!!")

            #return to the save directory
            goto_file_explorer_callback()

        roboprinter.robosm.current = "File_Explorer"

        save_dict = {
                'callback' : save_to_dir,
                'icon' : "Icons/Files_Icons/File_Options/Next.png"
                }
        self.show_only_folders_callback(save_dict, back_to_name=back_to_name)
        
    def order_buttons(self, gcode, stl, firmware, folders, **kwargs):
        sorting_option = self.settings.get(['sorting_config'])        

        reverse = False
        key = 'name'

        #sort by type
        if sorting_option['sort'] == lang.pack['Files']['Sort_Files']['Type']:
            #Logger.info("Sorting By Type!")
            #sort all filetypes by name
            sorted_gcode = sorted(gcode, key=lambda file: file['name'].lower())
            sorted_stl = sorted(stl, key=lambda file: file['name'].lower())
            sorted_firmware = sorted(firmware, key=lambda file: file['name'].lower())
            sorted_folders = sorted(folders, key=lambda file: file['name'].lower())

            #'STL first', 'GCODE first', 'Hex first', 'Folders first'
            if sorting_option['modify'] == lang.pack['Files']['Sort_Files']['Type_Options']['Folder']:
                return sorted_folders + sorted_gcode + sorted_stl + sorted_firmware
            elif sorting_option['modify'] == lang.pack['Files']['Sort_Files']['Type_Options']['GCODE']:
                return sorted_gcode + sorted_folders + sorted_stl + sorted_firmware
            elif sorting_option['modify'] == lang.pack['Files']['Sort_Files']['Type_Options']['STL']:
                return sorted_stl + sorted_folders + sorted_gcode + sorted_firmware
            elif sorting_option['modify'] == lang.pack['Files']['Sort_Files']['Type_Options']['HEX']:
                return sorted_firmware + sorted_folders + sorted_gcode + sorted_stl
        #Sort Alphabetically
        elif sorting_option['sort'] == lang.pack['Files']['Sort_Files']['Alphabet']:
            #Logger.info("Sorting Alphabetically!")
            if sorting_option['modify'] == lang.pack['Files']['Sort_Files']['Alphabet_Options']['Z2A']:
                reverse = True

            key = 'name'

            unsorted_files = gcode + stl + firmware + folders

            #This needs it's own sorting function because it needs to be case insensitive while sorting alphabetically
            sorted_files = sorted(unsorted_files, key=lambda file: file[key].lower(), reverse=reverse)
        
            return sorted_files

        #sort by size
        elif sorting_option['sort'] == lang.pack['Files']['Sort_Files']['Size']:
            #Logger.info("Sorting By Size!")
            if sorting_option['modify'] == lang.pack['Files']['Sort_Files']['Size_Options']['L2S']:
                reverse = True

            key = 'size'
            unsorted_files = gcode + stl + firmware + folders

            def get_folder_size(start_path = '.'):
                try:
                    total_size = 0
                    for dirpath, dirnames, filenames in os.walk(start_path):
                        for f in filenames:
                            fp = os.path.join(dirpath, f)
                            total_size += os.path.getsize(fp)
                    return total_size

                except Exception as e:
                    Logger.info("File no longer exists or Someone pulled the USB drive before fully loading")
                    return 0
                


            def detirmine_if_item_has_size(item):
                if 'size' in item:
                    return True
                else:
                    for x in range(0,len(unsorted_files)):
                        if item['name'] == unsorted_files[x]['name']:
                            meta = self.storage.get_metadata(item['path'])
                            if meta != None and key in meta:
                                unsorted_files[x][key] = meta[key] #if meta data has size key
                                
                            elif item['type'] == 'folder':
                                path = self.storage.path_on_disk(item['path'])
                                size = get_folder_size(path)
                                unsorted_files[x][key] = str(size) #if the type is folder then get the size of the dir

                            else:
                                path = self.storage.path_on_disk(item['path'])
                                try:
                                    size = os.path.getsize(path)
                                except Exception as e:
                                    Logger.info("File no longer exists or Someone pulled the USB drive before fully loading")
                                    size = "0"
                                unsorted_files[x][key] = str(size) #if the file is anything else just grab it's size
                            break
                    return False

            #protection in case there is no size. This makes a list of all items without the keyword size,
            #but the function adds it back in. Originally I did something with this array, but now it just 
            #acts as a for loop. I could turn it into a for loop, but it looks cooler this way and it has
            #no impact on time performance.
            [x for x in unsorted_files if not detirmine_if_item_has_size(x)] 


            sorted_files = sorted(unsorted_files, key=lambda file: int(file[key]), reverse=reverse)

            return sorted_files
        #sort by date
        elif sorting_option['sort'] == lang.pack['Files']['Sort_Files']['Date']:
            #Logger.info("Sorting By Date!")
            if sorting_option['modify'] == lang.pack['Files']['Sort_Files']['Date_Options']['New']:
                reverse = True

            key = 'date'

            #Folders don't have any date meta data
            unsorted_files = gcode + stl + firmware
            sorted_folders = sorted(folders, key=lambda file: file['name'])

            sorted_files = sorted(unsorted_files, key=lambda file: file[key], reverse=reverse)
        
            return sorted_files + sorted_folders



        
        
        
        

    def next_directory(self, name):
        if self.directory.goto_next_directory(name):

            self.current_title = name

            self.update_file_screen()
            roboprinter.screen_controls.update_title(self.current_title)
        else:
            Logger.info("Not and Option!!!!! " + str(name))

    def up_one_directory(self, exit=False, **kwargs):
        def return_to_previous():
            if self.directory.return_to_previous_directory():
                
                self.current_title = self.directory.dir_name
                self.update_file_screen()
                roboprinter.screen_controls.update_title(self.current_title)
            else:
                Logger.info("Cant go back any farther! Returning to main screen")
    
                #go back to main
                if 'file_callback' in session_saver.saved:
                    session_saver.saved['file_callback']() #this will update the size of the directory
                roboprinter.robosm.go_back_to_main('files_tab')

        #checks to see if exit is true, if it is then it will exit on the selected directory(Only USB currently). If it is not true then it
        #will exit on the root directory
        if exit:
            if self.directory.dir_name == self.exit_name:
                Logger.info("Cant go back any farther! Returning to main screen")

                #go back to main
                if 'file_callback' in session_saver.saved:
                    session_saver.saved['file_callback']() #this will update the size of the directory
                roboprinter.robosm.go_back_to_main('files_tab')
            else:
                return_to_previous()

        else:
            return_to_previous()

    def set_exit(self):
        self.exit_name = self.directory.dir_name

    def set_sorting_configuration(self, config):
        self.sorting_config = config




    

