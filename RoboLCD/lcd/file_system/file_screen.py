# -*- coding: utf-8 -*-
# @Author: Matt Pedler
# @Date:   2017-09-29 15:09:04
# @Last Modified by:   Matt Pedler
# @Last Modified time: 2017-10-27 13:20:24
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
from kivy.uix.modalview import ModalView
from kivy.clock import Clock
from kivy.uix.widget import Widget
from kivy.uix.popup import Popup
from kivy.logger import Logger
from kivy.core.window import Window
from kivy.uix.vkeyboard import VKeyboard
from RoboLCD.lcd.Language import lang


#python
import math
import os
import shutil
import re
from datetime import datetime
import collections
import traceback
from functools import partial

#RoboLCD
from RoboLCD import roboprinter
from RoboLCD.lcd.pconsole import pconsole
from RoboLCD.lcd.Language import lang
from RoboLCD.lcd.session_saver import session_saver
from RoboLCD.lcd.common_screens import Error_Popup
from RoboLCD.lcd.connection_popup import Zoffset_Warning_Popup


#octoprint
import octoprint.filemanager

class StandardFileButton(Button):
    callback = ObjectProperty(None)
    icon = StringProperty("Icons/Printer Status/blank-warning.png")
    filename = StringProperty('')
    date = StringProperty('')
    blue_color = ObjectProperty([0.41015625, 0.69921875, 0.90234375, 1])
    black_color = ObjectProperty([0.0,0.0,0.0,0.0])
    selected_color = ObjectProperty([0,0,0,0])

    def __init__(self, file_data=None, callback=None, icon="Icons/Printer Status/blank-warning.png", **kwargs):
        super(StandardFileButton, self).__init__(**kwargs)
        self.icon = icon
        self.file_data = file_data
        self.callback = callback
        self.settings = roboprinter.printer_instance._settings
       
    def file_on_release(self):
        if self.callback != None and self.file_data != None:
            self.callback(self.file_data)

    def update_callback(self, callback):
        self.callback = callback

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
        amount = int(size/factor)
        return str(amount) + suffix

    def update_file_data(self, file_data):
        if file_data != None:
            self.file_data = file_data
            self.filename = self.file_data['name']
            self.path = self.file_data['path']
            #get the sort order
            sorting_option = self.settings.get(['sorting_config'])
            measurement = 'date'
            if sorting_option['sort'] == lang.pack['Files']['Sort_Files']['Size']:
                measurement = 'size'
    
            if self.file_data['type'] != 'folder':
                #apply either date or size depending on the size
                if measurement == 'date':
                    self.date = datetime.fromtimestamp(int(self.file_data['date'])).strftime("%b %d")
                elif measurement == 'size':
                    self.date = self.get_size(int(self.file_data['size']))
                #Format spacing between filename and date
            else:
                if measurement == 'size':
                    self.date = self.get_size(int(self.file_data['size']))
                else:
                    self.date = ''
    
            #set the icon
            if self.file_data['type'] == 'folder':
                self.icon = "Icons/Files_Icons/Folder.png"
            elif self.file_data['type'] == 'firmware':
                self.icon = "Icons/Files_Icons/Hex.png"
            elif self.file_data['type'] == 'model':
                self.icon = "Icons/Files_Icons/File.png"
            elif self.file_data['type'] == "machinecode" :
                self.icon = "Icons/Files_Icons/Gcode3.png"

            if 'selected' in self.file_data:
                self.select(self.file_data['selected'])
            else:
                self.selected_color = self.black_color #make sure the outline gets gone good girl
        else:
            self.filename = ''
            self.path = ''
            self.date = ''
            self.file_data = None
            self.icon = "Icons/Printer Status/blank-warning.png"
            self.selected_color = self.black_color

    def update(self):
        self.update_file_data(self.file_data)

    def select(self, selected):
        if not selected:
            #set the icon
            self.selected_color = self.black_color
            if self.file_data['type'] == 'folder':
                self.icon = "Icons/Files_Icons/Folder.png"
            elif self.file_data['type'] == 'firmware':
                self.icon = "Icons/Files_Icons/Hex.png"
            elif self.file_data['type'] == 'model':
                self.icon = "Icons/Files_Icons/File.png"
            elif self.file_data['type'] == "machinecode" :
                self.icon = "Icons/Files_Icons/Gcode3.png"
        else:
            if self.file_data['type'] == "machinecode" :
                self.icon = "Icons/Files_Icons/Gcode selected.png"
            elif self.file_data['type'] == 'folder':
                self.icon = "Icons/Files_Icons/Folder selected.png"
            elif self.file_data['type'] == 'model':
                self.icon = "Icons/Files_Icons/STL selected.png"
            elif self.file_data['type'] == 'firmware':
                self.icon = "Icons/Files_Icons/Hex selected.png"

            self.selected_color = self.blue_color

class File_Progress(BoxLayout):
    """docstring for File_Progress"""
    moving_file = StringProperty(lang.pack['Files']['File_Progress']['Waiting'])
    progress = StringProperty("[size=40]0%")
    callback = ObjectProperty(None)
    title = StringProperty('Deleting')
    progress_number = NumericProperty(0)
    progress_width = NumericProperty(1)

    button_state = BooleanProperty(True)
    replace_text = StringProperty(lang.pack['Files']['File_Progress']['Replace'])
    keep_both_text = StringProperty(lang.pack['Files']['File_Progress']['Keep'])
    skip_text = StringProperty(lang.pack['Files']['File_Progress']['Skip'])
    replace = ObjectProperty(None)
    keep_both = ObjectProperty(None)
    skip = ObjectProperty(None)
    file_exists = StringProperty("[size=30]" + lang.pack['Files']['File_Progress']['In_Progress'])

    def __init__(self, **kwargs):
        super(File_Progress, self).__init__()
        
    def update_title(self, title):
        self.title = title

    def update_file(self, filename):
        self.moving_file = filename

    def update_progress(self, progress):
        self.progress_width = self.ids.progress_bar_goes_here.width
        self.progress_number = (float(progress) / 100.00) * float(self.progress_width)
        p_transformed = int(progress)
        self.progress = '[size=40]{}'.format(p_transformed) + roboprinter.lang.pack['Printer_Status']['Percent'] + '[/size]'

class Empty_Popup(ModalView):
    """docstring for Empty_Popup"""
    popup_object = ObjectProperty(None)
    def __init__(self, popup_object):
        super(Empty_Popup, self).__init__()
        self.popup_object = popup_object
        self.add_widget(self.popup_object)

    def show(self):
        self.open()
    def hide(self):
        self.dismiss()

class StandardFileView(BoxLayout):
    """
       docstring for StandardFileView
       This just shows a filename in a back button screen
    """
    call_function = ObjectProperty(None)
    file_data = ObjectProperty(None)
    body_text = StringProperty('')
    button_state = BooleanProperty(False)

    def __init__(self, file_data, body_text, call_function=None):
        self.file_data = file_data
        self.call_function = call_function
        self.body_text = body_text
        if roboprinter.printer_instance._printer.is_ready() and not roboprinter.printer_instance._printer.is_printing() and not roboprinter.printer_instance._printer.is_paused():
            self.button_state = False
        else:
            self.button_state = True
        super(StandardFileView, self).__init__()
        

    def button_function(self):
        if self.call_function != None:
            self.call_function(self.file_data)

class FolderButton(Button):
    file_function = ObjectProperty(None)
    name = StringProperty('')
    def __init__(self, file_data, callback_function, **kwargs):
        super(FolderButton, self).__init__()
        self.name = file_data['name']
        self.file_data = file_data
        self.file_function = callback_function
        

    def folder_on_release(self):
        self.file_function(self.name)

'''
This Buttons work with other buttons to achieve a common goal like selecting multiple files, or 
Setting a Sort Order for buttons. 
'''
            
class File_Option_Button(Button):
    """docstring for File_Option_Button"""
    default_icon = StringProperty("")
    selected_icon= StringProperty("")
    name = StringProperty("Error")
    extra_content = BooleanProperty(False)
    selected_icon = BooleanProperty(False)
    callback = ObjectProperty(None)
    observer = ObjectProperty(None)
    icon = StringProperty("Icons/Printer Status/blank-warning.png")
    option_list = ObjectProperty([''])
    ec_text = StringProperty("")
    list_pos = NumericProperty(0)
    blue_color = ObjectProperty([0.41015625, 0.69921875, 0.90234375, 1])
    black_color = ObjectProperty([0.0,0.0,0.0,0.0])
    selected_color = ObjectProperty([0,0,0,0])
    bc_width = NumericProperty(0)

    def __init__(self, default_icon='', 
                       selected_icon='', 
                       name="Error", 
                       extra_content=False, 
                       option_list=[''],
                       selected=False, 
                       callback=None, 
                       observer=None, 
                       can_toggle=False,
                       file_data=None,
                       **kwargs ):
        
        #set up button
        self.default_icon = default_icon if default_icon != '' else "Icons/Printer Status/blank-warning.png"
        self.selected_icon = selected_icon if selected_icon != '' else self.default_icon
        self.icon = default_icon 
        self.original_name = name
        self.extra_content = extra_content
        self.callback = callback
        self.observer = observer
        self.selected = selected
        self.can_toggle = can_toggle
        self.option_list = option_list
        self.list_pos = 0
        self.name = name
        self.file_data = file_data

        super(File_Option_Button, self).__init__()

        #populate the extra content
        if self.extra_content:
            self.content = self.ids.extra_content
            self.bc_width = self.content.width
        else:
            self.content = self.ids.extra_content
            self.content.size_hint_x = 0
            self.content.width = 0


        #connect with the observer if there is one
        if self.observer != None:
            self.observer.register_callback(self.original_name, self.update_selected)

        #select self if selected
        self.select(self.selected)

    def up_list(self):
        self.list_pos += 1

        if self.list_pos >= len(self.option_list):
            self.list_pos = 0

        self.ec_text = "[size=30]" + self.option_list[self.list_pos]



    def select(self, set_select):
        if set_select:
            #change aesthetics
            #Logger.info("Selecting " + str(self.original_name))
            self.selected_color = self.blue_color
            self.icon = self.selected_icon
            if self.observer != None:
                self.observer.change_button(self.original_name)

            if self.extra_content:
                self.ec_text = "[size=30]" + self.option_list[self.list_pos]
                self.content.size_hint_x = 1
                self.content.width = self.bc_width
        else:
            #Logger.info("Deselecting " + str(self.original_name))
            self.selected_color = self.black_color
            self.icon = self.default_icon
            if self.extra_content:
                self.name = self.original_name
                self.content.size_hint_x = 0
                self.content.width = 0

        self.selected = set_select

    def update_selected(self, name):
        if name != self.original_name:
            self.select(False)

    def on_press_button(self):
        #toggle selection
        #Logger.info("Pressed the Button!")
        if self.callback == None:
            if self.can_toggle:
                self.select(not self.selected)
            else:
                self.select(True)
        else:
            self.callback()

class Up_Down_Buttons(BoxLayout):
    """docstring for Up_Down_Buttons
       This class is supposed to be taken over by a parent class to scroll through a list of options.
    """
    def __init__(self):
        super(Up_Down_Buttons, self).__init__()
        pass

    def up(self):
        pass

class File_Counter(BoxLayout):
    """docstring for File_Counter"""
    file_count = StringProperty("0")
    files_selected = StringProperty(lang.pack['Files']['Modify_Files']['Files_Selected'])
    def __init__(self, file_count):
        super(File_Counter, self).__init__()
        self.file_count = file_count

    def update_count(self, count):
        self.file_count = count

'''
Scroll_Box_File_List is meant to scroll through a dictionary of the files. This will save space as well as make refreshing files easier

'''
class Scroll_Box_File_List(BoxLayout):
    """docstring for Scroll_Box_Even"""
    position = 0
    max_pos = 0
    buttons = []
    up_icons = ["Icons/Up-arrow-grey.png", "Icons/Up-arrow-blue.png"]
    down_icons = ["Icons/Down-arrow-grey.png", "Icons/Down-arrow-blue.png"]
    up_icon = ObjectProperty("Icons/Up-arrow-grey.png")
    down_icon = ObjectProperty("Icons/Down-arrow-grey.png")
    callback = ObjectProperty(None)
    def __init__(self, file_list, button_callback):
        super(Scroll_Box_File_List, self).__init__()
        self.up_event = None
        self.down_event = None
        self.grid = self.ids.content
        self.max_pos = len(file_list) - 4
        self.file_list = file_list
        self.original_scroll_size = self.scroll.size_hint_x
        self.original_scroll_width = self.scroll.width
        self.file_buttons = [self.ids.button_1, self.ids.button_2, self.ids.button_3, self.ids.button_4]
        self.callback = button_callback

        self.ids.button_up.bind(state=self.up_button_state)
        self.ids.button_down.bind(state=self.down_button_state)

        for button in self.file_buttons:
            button.update_callback(self.callback)
        if len(self.file_list) <= 4:
            self.scroll.size_hint_x = 0
            self.scroll.width = 0.1
        self.populate_buttons()

    def update_callback(self, callback):
        for button in self.file_buttons:
            button.update_callback(callback)

    def update_button_status(self):
        for button in self.file_buttons:
            button.update()

    def repopulate_for_new_screen(self):
        self.position = 0
        self.max_pos = len(self.file_list) - 4
        self.populate_buttons()

    def populate_buttons(self):
        
        for x in range(0,4):
            if self.position + x < len(self.file_list):
                self.file_buttons[x].update_file_data(self.file_list[self.position + x])
            else:
                self.file_buttons[x].update_file_data(None)

        self.check_for_scroll()

    def up_button_state(self, instance, value):
        if value == 'down':
            self.on_up_press()
        else:
            self.on_up_release()


    def up_button(self):
        # Logger.info("Up hit")
        self.position -= 1
        if self.position < 0:
            self.position = 0
            self.up_event.cancel()
        self.populate_buttons()

    #every 0.2 seconds scroll up until the user releases the button
    def on_up_press(self):

        #change Color
        self.up_icon = self.up_icons[1]

        if self.up_event != None:
            self.up_event.cancel()
        if self.down_event != None:
            self.down_event.cancel()
        self.up_event = Clock.schedule_interval(self.on_up_clock, 0.2)


    def on_up_release(self):
        #change Color
        self.up_icon = self.up_icons[0]
        self.up_event.cancel()
        self.up_button()

    def on_up_clock(self,dt):
        self.up_button()

    def down_button_state(self, instance, value):
        if value == 'down':
            self.on_down_press()
        else:
            self.on_down_release()
        

    def down_button(self):
        # Logger.info("down hit")
        self.position += 1
        if self.position > self.max_pos:
            self.position = self.max_pos
            self.down_event.cancel()
        self.populate_buttons()

    #every 0.2 seconds scroll down until the user releases the button
    def on_down_press(self):
        #change Color
        self.down_icon = self.down_icons[1]
        if self.up_event != None:
            self.up_event.cancel()
        if self.down_event != None:
            self.down_event.cancel()
        self.down_event = Clock.schedule_interval(self.on_down_clock, 0.2)

    def on_down_release(self):
        #change Color
        self.down_icon = self.down_icons[0]
        self.down_event.cancel()
        self.down_button()

    def on_down_clock(self, dt):
        self.down_button()

    def check_for_scroll(self):
        if len(self.file_list) <= 4:
            self.scroll.size_hint_x = 0
            self.scroll.width = 0.1
        else:
            self.scroll.size_hint_x = self.original_scroll_size
            self.scroll.width = self.original_scroll_width


'''
Keyboard Input uses the keyboard and file_bb to create an input interface
'''
class KeyboardInput_file_bb(FloatLayout):
    kbContainer = ObjectProperty()
    keyboard_callback = ObjectProperty(None)
    default_text = StringProperty('')

    def __init__(self, keyboard_callback = None, default_text = '', name = 'keyboard_screen', title=lang.pack['Files']['Keyboard']['Default_Title'], back_destination=None,**kwargs):
        super(KeyboardInput_file_bb, self).__init__(**kwargs)
        self.default_text = default_text
        self.back_destination = back_destination
        self.title = title
        if self.back_destination == None:
            raise Exception("back destination needs to be set with a screen dictionary to go back to")

        self.first_press = False
        roboprinter.screen_controls.set_screen_content(self, #content
                                                       self.title, #title of content
                                                       back_function=self.previous_screen, #back button function
                                                       option_function=self.next_screen,
                                                       option_icon="Icons/Files_Icons/File_Options/Next.png" ) #option Button function

        self._keyboard = None
        self._set_keyboard('keyboards/abc.json')

        self.keyboard_callback = keyboard_callback
        if self.keyboard_callback == None:
            raise Exception('keyboard callback needs to be set')

    def previous_screen(self):
        #turn off keyboard
        self.close_screen()
        #go back to screen
        roboprinter.screen_controls.populate_old_screen(self.back_destination)

    def next_screen(self):
        self.close_screen()
        self.keyboard_callback(self.ids.fname.text)

    def close_screen(self):
        if self._keyboard:
            Window.release_all_keyboards()  

    def _set_keyboard(self, layout):
        #Dock the keyboard
        kb = Window.request_keyboard(self._keyboard_close, self)
        if kb.widget:
            self._keyboard = kb.widget
            self._keyboard.layout = layout
            self._style_keyboard()
        else:
            self._keyboard = kb
        self._keyboard.bind(on_key_down=self.key_down)
        Logger.info('Keyboard: Init {}'.format(layout))

    def _keyboard_close(self):
        if self._keyboard:
            self._keyboard.unbind(on_key_down=self.key_down)
            self._keyboard = None

    def _style_keyboard(self):
        if self._keyboard:
            self._keyboard.margin_hint = 0,.02,0,0.02
            self._keyboard.height = 250
            self._keyboard.key_background_normal = 'Icons/Keyboard/keyboard_button.png'
            self.scale_min = .4
            self.scale_max = 1.6


    def key_down(self, keyboard, keycode, text, modifiers):
        """
        Callback function that catches keyboard events and writes them as password
        """
        # Writes to self.ids.password.text
        if self.ids.fname.text == self.default_text and not self.first_press: #clear stub text with first keyboard push
            self.ids.fname.text = ''
        if keycode == 'backspace':
            self.ids.fname.text = self.ids.fname.text[:-1]
        elif keycode == 'capslock' or keycode == 'normal' or keycode == 'special':
            pass
        elif keycode == 'toggle':
            self.toggle_keyboard()
        else:
            self.ids.fname.text += text

        #detect first press
        if not self.first_press:
            self.first_press = True

    def toggle_keyboard(self):
        if self._keyboard.layout == "keyboards/abc.json":
            self._keyboard.layout = "keyboards/123.json"
        else:
            self._keyboard.layout = "keyboards/abc.json"

class PrintFile(GridLayout):
    """
    This class encapsulates the dynamic properties that get rendered on the PrintFile and the methods that allow the user to start a print.
    """
    name = StringProperty('')
    file_name = ObjectProperty(None)
    print_layer_height = ObjectProperty(None)
    print_layers = ObjectProperty(None)
    print_length = ObjectProperty(None)
    hours = NumericProperty(0)
    minutes = NumericProperty(0)
    seconds = NumericProperty(0)
    infill = ObjectProperty(None)
    file_path = ObjectProperty(None)
    status = StringProperty('--')
    subtract_amount = NumericProperty(30)
    current_z_offset = StringProperty('--')
    meta_status = StringProperty(lang.pack['File_Screen']['Get_Meta'])

    def __init__(self, file_data, **kwargs):
        super(PrintFile, self).__init__(**kwargs)
        self.queued_data = False
        self.found_meta_data = False
        self.exit = False
        self.file = file_data
        self.file_path = self.file['path']
        self.file_name = self.file['name']
        self.status = self.is_ready_to_print()

        Clock.schedule_interval(self.update, .2)

        self.current_z_offset = str("{0:.1f}".format(float(pconsole.home_offset['Z'])))

        cura_meta = self.check_saved_data()
        self.print_layer_height = '--'
        self.print_layers = '--'
        self.infill = '--'
        self.hours = 0
        self.minutes = 0
        self.seconds = 0
        self.populate_meta_data(cura_meta)

        

    def populate_meta_data(self, cura_meta):
        if cura_meta != False:
            if 'layer height' in cura_meta:
                self.print_layer_height = cura_meta['layer height']
            else:
                self.print_layer_height = "--"
            if 'layers' in cura_meta:
                self.print_layers = cura_meta['layers']
            else:
                layers = "--"
            if 'infill' in cura_meta:
                self.infill = cura_meta['infill']
            else:
                infill = "--"

            if 'time' in cura_meta:
                self.hours = int(cura_meta['time']['hours'])
                self.minutes = int(cura_meta['time']['minutes'])
                self.seconds = int(cura_meta['time']['seconds'])
            else:
                self.hours = 0
                self.minutes = 0
                self.seconds = 0

        else:
            self.print_layer_height = '--'
            self.print_layers = '--'
            self.infill = '--'
            self.hours = 0
            self.minutes = 0
            self.seconds = 0

    #This function will check the filename against saved data on the machine and return saved meta data
    def check_saved_data(self):
        self.octo_meta = roboprinter.printer_instance._file_manager
        saved_data = self.octo_meta.get_metadata(octoprint.filemanager.FileDestinations.LOCAL , self.file_path)


        if 'robo_data' in saved_data:
            self.found_meta_data = True
            return saved_data['robo_data']
            
        else:
            #queue the file for processing. This also checks to see if we have already sent the file over to be analyzed
            if not self.queued_data:
                self.queued_data = True
                mock_file_system = {
                    self.file['name'] : self.file
                }
                roboprinter.printer_instance.start_analysis(files=mock_file_system)

            return False


    def update(self, dt):
        if roboprinter.printer_instance._printer.is_paused():
            self.status = 'PRINTER IS BUSY'
        else:
            self.status = self.is_ready_to_print()
        #toggle between button states
        if self.status == 'PRINTER IS BUSY' and self.ids.start.background_normal == "Icons/green_button_style.png":
            self.ids.start.background_normal = "Icons/red_button_style.png"
            self.ids.start.button_text = '[size=30]' + roboprinter.lang.pack['Files']['File_Status']['Busy'] + '[/size]'
            self.ids.start.image_icon = 'Icons/Manual_Control/printer_button_icon.png'
         
        elif self.status == "READY TO PRINT" and self.ids.start.background_normal == "Icons/red_button_style.png":
            self.ids.start.background_normal = "Icons/green_button_style.png"
            self.ids.start.button_text = '[size=30]' + roboprinter.lang.pack['Files']['File_Status']['Start'] + '[/size]'
            self.ids.start.image_icon = 'Icons/Manual_Control/start_button_icon.png'

        #check for meta data and update
        if not self.found_meta_data: #no need to keep on looking if we have found meta data
            cura_meta = self.check_saved_data()
            self.populate_meta_data(cura_meta)

            
            self.meta_status += "."
            if self.meta_status.find('....') != -1:
                self.meta_status = lang.pack['File_Screen']['Get_Meta']
        else:
            self.meta_status = ''

        #check for exit
        if self.exit:
            return False

    def exit_function(self, exit_callback):
        self.exit = True
        exit_callback()
            

    def start_print(self, *args):
        #Throw a popup to display the ZOffset if the ZOffset is not in the range of -20 - 0 
        try:
            if self.status == "READY TO PRINT":
                _offset = float(pconsole.home_offset['Z'])

                if _offset <= -20.0 or _offset >= 0.0:
                    zoff = Zoffset_Warning_Popup(self)
                    zoff.open()
                else:
                    """Starts print but cannot start a print when the printer is busy"""
                    Logger.info(self.file_path)
                    self.force_start_print()
        except Exception as e:
            #raise error
            error = Error_Popup(roboprinter.lang.pack['Files']['File_Error']['Title'],roboprinter.lang.pack['Files']['File_Error']['Body'],callback=partial(roboprinter.robosm.go_back_to_main, tab='printer_status_tab'))
            error.open()
            Logger.info("Start Print Error")
            Logger.info("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! "+ str(e))
            traceback.print_exc()

    def force_start_print(self, *args):
        """Starts print but cannot start a print when the printer is busy"""
        try:
            path_on_disk = roboprinter.printer_instance._file_manager.path_on_disk(octoprint.filemanager.FileDestinations.LOCAL, self.file_path)
            roboprinter.printer_instance._printer.select_file(path=path_on_disk, sd=False, printAfterSelect=True)
        except Exception as e:
            #raise error
            error = Error_Popup(roboprinter.lang.pack['Files']['File_Error']['Title'],roboprinter.lang.pack['Files']['File_Error']['Body'],callback=partial(roboprinter.robosm.go_back_to_main, tab='printer_status_tab'))
            error.open()
            Logger.info("Force Start Print Error")
            Logger.info("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! "+ str(e))
            traceback.print_exc()

        self.exit = True


    def is_ready_to_print(self):
        """ whether the printer is currently operational and ready for a new print job"""
        is_ready = roboprinter.printer_instance._printer.is_ready()
        printing = roboprinter.printer_instance._printer.is_printing()
        if is_ready and not printing:
            return 'READY TO PRINT'
        else:
            return 'PRINTER IS BUSY'






    
     