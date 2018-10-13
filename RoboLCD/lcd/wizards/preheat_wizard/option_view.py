# -*- coding: utf-8 -*-
# @Author: Matt Pedler
# @Date:   2017-10-05 11:40:54
# @Last Modified by:   Matt Pedler
# @Last Modified time: 2018-01-31 11:46:46


#kivy
from kivy.uix.button import Button
from kivy.properties import StringProperty, NumericProperty, ObjectProperty, BooleanProperty
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.uix.togglebutton import ToggleButton
from kivy.logger import Logger
from kivy.clock import Clock

#RoboLCD
from RoboLCD import roboprinter
from RoboLCD.lcd.pconsole import pconsole
from RoboLCD.lcd.printer_jog import printer_jog
from RoboLCD.lcd.scrollbox import Scroll_Box_Even
from RoboLCD.lcd.Language import lang
from RoboLCD.lcd.common_screens import Modal_Question_No_Title, KeyboardInput, Keypad, Extruder_Selector
from RoboLCD.lcd.session_saver import session_saver
from RoboLCD.lcd.connection_popup import Info_Popup, Error_Popup

from RoboLCD.lcd.wizards.preheat_wizard.preheat_buttons import Preheat_Button, Simple_Button, Dual_Button

#Python
from functools import partial
import thread

#This class is the view for the preheat options
class Option_View(BoxLayout):
    button_padding = ObjectProperty([0,0,0,0])
    button_spacing = ObjectProperty(50)

    def __init__(self, option=None, dual=False, callback = None, delete_callback = None, back_destination = None, back_button_screen=None, group=None, **kwargs):
        super(Option_View, self).__init__()
        self.model = roboprinter.printer_instance._settings.get(['Model'])
        self.back_destination = back_destination
        self.callback = callback
        self.delete_callback = delete_callback
        self.confirm_overwrite = False
        self.bb = back_button_screen
        self.group = group
        Logger.info("Option_View has group: " + str(self.group))

        self.option = option
        self.dual = dual
        if self.option != None:
            #populate fields and make buttons
            #add save and delete button
            if not self.dual:
                self.populate_option(option)
                self.original_option = option
            else:
                #populate the dual version of this class
                self.populate_dual_option(option)
                self.original_option = option
        else:
            #populate fields with default values
            #add only a save button
            if not self.dual:
                self.populate_default()
                self.original_option = None
            else:
                #Populate the dual default
                self.populate_dual_default()
                self.original_option = None

    #This populates a known option with preset variables
    def populate_option(self, option):
        #get presets
        preset_options = roboprinter.printer_instance._settings.get(['Temp_Preset'])

        self.selected_option = {option: preset_options[option]}
        Logger.info("Selected Preset is: " + str(self.selected_option))

        #make options
        name = next(iter(self.selected_option))
        name_title = lang.pack['Preheat']['Edit_Preset']['Name']
        name_body = lang.pack['Preheat']['Edit_Preset']['Set_Name']

        ext1 = self.selected_option[name]['Extruder1']
        ext1_title = lang.pack['Preheat']['Edit_Preset']['Ext']
        ext1_body = lang.pack['Preheat']['Edit_Preset']['Ext_Body']

        bed = self.selected_option[name]['Bed']
        bed_title = lang.pack['Preheat']['Edit_Preset']['Bed']
        bed_body = lang.pack['Preheat']['Edit_Preset']['Bed_Body']

        #make buttons with the options
        self.name_button = Preheat_Button(name_title, name, name_body, self.show_keyboard)
        self.ext1_button = Preheat_Button(ext1_title, ext1, ext1_body, self.show_keypad)

        #if we are a C2 add a label
        if self.model == "Robo R2":
            self.bed_button =  Preheat_Button(bed_title, bed, bed_body, self.show_keypad)
        else:
            self.bed_button = Preheat_Button('','','',self.placeholder)

        #make save and delete buttons

        save = Simple_Button(lang.pack['Preheat']['Edit_Preset']['Save'], "Icons/blue_button_style.png", self.save_preset)
        delete = Simple_Button(lang.pack['Preheat']['Edit_Preset']['Delete'], "Icons/red_button_style.png", self.delete_preset)

        #push buttons to the grid
        button_list = [self.name_button, self.ext1_button, self.bed_button]

        for button in button_list:
            self.ids.button_box.add_widget(button)

        #push save and delete to grid
        button_list = [save, delete]

        for button in button_list:
            self.ids.modal_box.add_widget(button)

        #adjust button padding for two buttons
        self.button_padding = [50,15,50,15]
        self.button_spacing = 50

    #This populates a known option with preset variables
    def populate_dual_option(self, option):
        #get presets
        preset_options = roboprinter.printer_instance._settings.get(['Dual_Temp_Preset'])
        self.selected_option = {option: preset_options[option]}
        Logger.info("Selected Preset is: " + str(self.selected_option))


        name_title = lang.pack['Preheat']['Edit_Preset']['Name']
        name = next(iter(self.selected_option))
        name_body = lang.pack['Preheat']['Edit_Preset']['Set_Name']

        ext1 = self.selected_option[name]['Extruder1']
        ext1_title = lang.pack['Preheat']['Edit_Preset_Dual']['Extruder1'] #+ str(ext1) + lang.pack['Preheat']['Celsius_Alone']
        ext1_body = lang.pack['Preheat']['Edit_Preset_Dual']['Ext1_Body']

        ext2 = self.selected_option[name]['Extruder2']
        ext2_title = lang.pack['Preheat']['Edit_Preset_Dual']['Extruder2'] #+ str(ext2) + lang.pack['Preheat']['Celsius_Alone']
        ext2_body = lang.pack['Preheat']['Edit_Preset_Dual']['Ext2_Body']

        bed = self.selected_option[name]['Bed']
        bed_title = lang.pack['Preheat']['Edit_Preset']['Bed'] #+ str(bed) + lang.pack['Preheat']['Celsius_Alone']
        bed_body = lang.pack['Preheat']['Edit_Preset']['Bed_Body']

         #make buttons with the options
        self.name_button = Preheat_Button(name_title, name, name_body, self.show_keyboard)
        self.ext1_button = Preheat_Button(ext1_title, ext1, ext1_body, self.show_keypad)
        self.ext2_button = Preheat_Button(ext2_title, ext2, ext2_body, self.show_keypad)

        self.dual_button = Dual_Button([self.ext1_button, self.ext2_button])

        #if we are a C2 add a label
        if self.model == "Robo R2":
            self.bed_button =  Preheat_Button(bed_title, bed, bed_body, self.show_keypad)
        else:
            self.bed_button = Preheat_Button('','','',self.placeholder)


        #make save and delete button
        save = Simple_Button(lang.pack['Preheat']['Edit_Preset']['Save'], "Icons/blue_button_style.png", self.save_preset)
        delete = Simple_Button(lang.pack['Preheat']['Edit_Preset']['Delete'], "Icons/red_button_style.png", self.delete_preset)
        #push buttons to the grid
        button_list = [self.name_button, self.dual_button, self.bed_button]

        for button in button_list:
            self.ids.button_box.add_widget(button)

        #push save and delete to grid
        button_list = [save, delete]

        for button in button_list:
            self.ids.modal_box.add_widget(button)

        #adjust button padding for two buttons
        self.button_padding = [50,15,50,15]
        self.button_spacing = 50


    #This populates a default option so we can save it later
    def populate_default(self):
        #make options
        self.selected_option = {lang.pack['Preheat']['Edit_Preset']['Name_Default'] : {

                                    'Extruder1': 0,
                                    'Bed': 0
                                    }
                                }

        name = lang.pack['Preheat']['Edit_Preset']['Name_Default']
        name_title = lang.pack['Preheat']['Edit_Preset']['Name']
        name_body = lang.pack['Preheat']['Edit_Preset']['Set_Name']

        ext1 = 0
        ext1_title = lang.pack['Preheat']['Edit_Preset']['Ext']
        ext1_body = lang.pack['Preheat']['Edit_Preset']['Ext_Body']

        bed = 0
        bed_title = lang.pack['Preheat']['Edit_Preset']['Bed']
        bed_body = lang.pack['Preheat']['Edit_Preset']['Bed_Body']

         #make buttons with the options
        self.name_button = Preheat_Button(name_title, name, name_body, self.show_keyboard)
        self.ext1_button = Preheat_Button(ext1_title, ext1, ext1_body, self.show_keypad)

        #if we are a C2 add a label
        if self.model == "Robo R2":
            self.bed_button =  Preheat_Button(bed_title, bed, bed_body, self.show_keypad)
        else:
            self.bed_button = Preheat_Button('','','',self.placeholder)


        #make save button
        save = Simple_Button(lang.pack['Preheat']['Edit_Preset']['Save'], "Icons/blue_button_style.png", self.save_preset)
        #push buttons to the grid
        button_list = [self.name_button, self.ext1_button, self.bed_button]

        for button in button_list:
            self.ids.button_box.add_widget(button)

        self.ids.modal_box.add_widget(save)

        #adjust button padding for one buttons
        self.button_padding = [200,15,200,15]
        self.button_spacing = 0



    #This populates a default option so we can save it later
    def populate_dual_default(self):
        #make options
        self.selected_option = {lang.pack['Preheat']['Edit_Preset']['Name_Default'] : {

                                    'Extruder1': 0,
                                    'Extruder2': 0,
                                    'Bed': 0
                                    }
                                }
        name_title = lang.pack['Preheat']['Edit_Preset']['Name']
        name = lang.pack['Preheat']['Edit_Preset']['Name_Default']
        name_body = lang.pack['Preheat']['Edit_Preset']['Set_Name']

        ext1 = 0
        ext1_title = lang.pack['Preheat']['Edit_Preset_Dual']['Extruder1'] #+ str(ext1) + lang.pack['Preheat']['Celsius_Alone']
        ext1_body = lang.pack['Preheat']['Edit_Preset_Dual']['Ext1_Body']

        ext2 = 0
        ext2_title = lang.pack['Preheat']['Edit_Preset_Dual']['Extruder2'] #+ str(ext2) + lang.pack['Preheat']['Celsius_Alone']
        ext2_body = lang.pack['Preheat']['Edit_Preset_Dual']['Ext2_Body']

        bed = 0
        bed_title = lang.pack['Preheat']['Edit_Preset']['Bed'] #+ str(bed) + lang.pack['Preheat']['Celsius_Alone']
        bed_body = lang.pack['Preheat']['Edit_Preset']['Bed_Body']

         #make buttons with the options
        self.name_button = Preheat_Button(name_title, name, name_body, self.show_keyboard)
        self.ext1_button = Preheat_Button(ext1_title, ext1, ext1_body, self.show_keypad)
        self.ext2_button = Preheat_Button(ext2_title, ext2, ext2_body, self.show_keypad)

        self.dual_button = Dual_Button([self.ext1_button, self.ext2_button])

        #if we are a C2 add a label
        if self.model == "Robo R2":
            self.bed_button =  Preheat_Button(bed_title, bed, bed_body, self.show_keypad)
        else:
            self.bed_button = Preheat_Button('','','',self.placeholder)


        #make save button
        save = Simple_Button(lang.pack['Preheat']['Edit_Preset']['Save'], "Icons/blue_button_style.png", self.save_preset)
        #push buttons to the grid
        button_list = [self.name_button, self.dual_button, self.bed_button]

        for button in button_list:
            self.ids.button_box.add_widget(button)

        self.ids.modal_box.add_widget(save)

        #adjust button padding for one buttons
        self.button_padding = [200,15,200,15]
        self.button_spacing = 0


    def placeholder(self, *args, **kwargs):
        Logger.info("Button Works")

    def show_keyboard(self, name, title=lang.pack['Preheat']['Keyboard']['Title']):
        #keyboard_callback = None, default_text = '', name = 'keyboard_screen', title=lang.pack['Keyboard']['Default_Title']
        KeyboardInput(keyboard_callback=self.get_keyboard_results,
                      default_text=name,
                      back_destination=roboprinter.robosm.current,
                      title=title,
                      back_button=self.bb,
                      group=self.group)

    def get_keyboard_results(self, result):
        def overwrite():
            Logger.info("Result is: " + str(result))
            name = next(iter(self.selected_option))

            if not self.dual:
                temp_option = {result:
                                {
                                    'Extruder1': self.selected_option[name]['Extruder1'],
                                    'Bed': self.selected_option[name]['Bed']
                                }
                              }
            else:
                temp_option = {result:
                                {
                                    'Extruder1' : self.selected_option[name]['Extruder1'],
                                    'Extruder2' : self.selected_option[name]['Extruder2'],
                                    'Bed': self.selected_option[name]['Bed']
                                }
                              }

            Logger.info(str(temp_option))

            self.selected_option = temp_option
            self.name_button.update_value(str(result))

            if self.bb == None:
                roboprinter.robosm.current = 'edit_preheat'
            else:
                Logger.info("Going back a page with group: " + str(self.group))
                if self.option != None:
                    self.bb.go_back_to_screen_with_title(lang.pack['Preheat']['Edit_Preset']['Title'])
                else:
                    self.bb.go_back_to_screen_with_title(lang.pack['Preheat']['Edit_Preset']['Add_Material'])

            self.confirm_overwrite = True

        def cancel():
            name = next(iter(self.selected_option))
            self.show_keyboard(name)

        #check if the result will overwrite an existing preset
        preheat_name = next(iter(self.selected_option))
        Logger.info("Result is: " + str(result) + " Name is: " + str(preheat_name))
        preheat_settings = roboprinter.printer_instance._settings.get(['Temp_Preset'])
        if result != preheat_name and result in preheat_settings:
            #make the modal screen
            body_text = lang.pack['Preheat']['Duplicate']['Body_Text'] + str(result) + lang.pack['Preheat']['Duplicate']['Body_Text1']
            modal_screen = Modal_Question_No_Title(body_text, lang.pack['Preheat']['Duplicate']['option1'] , lang.pack['Preheat']['Duplicate']['option2'] , overwrite, cancel)

            #make screen
            if self.bb == None:
                roboprinter.robosm._generate_backbutton_screen(name='duplicate_error',
                                                               title = lang.pack['Preheat']['Duplicate']['Title'],
                                                               back_destination='edit_preheat',
                                                               content=modal_screen)
            else:
                self.bb.make_screen(modal_screen,
                                 lang.pack['Preheat']['Duplicate']['Title'],
                                 option_function='no_option',
                                 group=self.group)
        else:
            overwrite()



    def show_keypad(self, value, title):
        if (title.find(lang.pack['Preheat']['Edit_Preset']['Ext']) != -1
            or title.find(lang.pack['Preheat']['Edit_Preset_Dual']['Extruder1']) != -1
            or title.find(lang.pack['Preheat']['Edit_Preset_Dual']['Extruder2']) != -1):
            #callback, number_length=3,name='keyboard_screen', title=lang.pack['Files']['Keyboard']['Default_Title']

            if title.find(lang.pack['Preheat']['Edit_Preset']['Ext']) != -1:
                Keypad(self.collect_ext1_key,
                       name='ext1_keyboard',
                       title=lang.pack['Preheat']['Keypad']['Title_ext1'],
                       make_screen=self.bb,
                       group=self.group)

            elif title.find(lang.pack['Preheat']['Edit_Preset_Dual']['Extruder1']) != -1:
                Keypad(self.collect_ext1_key,
                       name='ext1_keyboard',
                       title=lang.pack['Preheat']['Keypad']['Title_dual_ext1'],
                       make_screen=self.bb,
                       group=self.group)

            elif title.find(lang.pack['Preheat']['Edit_Preset_Dual']['Extruder2']) != -1:
                Keypad(self.collect_ext2_key,
                       name='ext1_keyboard',
                       title=lang.pack['Preheat']['Keypad']['Title_dual_ext2'],
                       make_screen=self.bb,
                       group=self.group)


        else:
            Keypad(self.collect_bed_key,
                   name='bed_keyboard',
                   title=lang.pack['Preheat']['Keypad']['Title_bed'],
                   make_screen=self.bb,
                   group=self.group)

    def collect_ext1_key(self, value):
        Logger.info("Ext1 Result is: " + str(value))
        if int(value) > 290:
            ep = Info_Popup(lang.pack['Preheat']['Errors']['Ext1_Error'], lang.pack['Preheat']['Errors']['Ext1_Body'])
            value = 290
            ep.show()
        name = next(iter(self.selected_option))


        self.selected_option[name]['Extruder1'] = int(value)
        self.ext1_button.update_value(int(value))
        if self.bb != None:
            if self.option != None:
                self.bb.go_back_to_screen_with_title(lang.pack['Preheat']['Edit_Preset']['Title'], group=self.group)
            else:
                self.bb.go_back_to_screen_with_title(lang.pack['Preheat']['Edit_Preset']['Add_Material'], group=self.group)

    def collect_ext2_key(self, value):
        #gather results
        Logger.info("Ext1 Result is: " + str(value))
        #Throw an error if the heat is too high
        if int(value) > 290:
            ep = Info_Popup(lang.pack['Preheat']['Errors']['Ext1_Error'], lang.pack['Preheat']['Errors']['Ext1_Body'])
            value = 290
            ep.show()
        name = next(iter(self.selected_option))

        #change the data model to reflect what the user chose
        self.selected_option[name]['Extruder2'] = int(value)
        self.ext2_button.update_value(int(value))

        #Go back to previous screen
        if self.bb!= None:
            if self.option != None:
                self.bb.go_back_to_screen_with_title(lang.pack['Preheat']['Edit_Preset']['Title'], group=self.group)
            else:
                self.bb.go_back_to_screen_with_title(lang.pack['Preheat']['Edit_Preset']['Add_Material'], group=self.group)


    def collect_bed_key(self, value):
        Logger.info("Bed Result is: " + str(value))
        if int(value) > 100:
            ep = Info_Popup(lang.pack['Preheat']['Errors']['Bed_Error'], lang.pack['Preheat']['Errors']['Bed_Body'])
            value = 100
            ep.show()
        name = next(iter(self.selected_option))

        self.selected_option[name]['Bed'] = int(value)
        self.bed_button.update_value(int(value))
        if self.bb != None:
            if self.option != None:
                self.bb.go_back_to_screen_with_title(lang.pack['Preheat']['Edit_Preset']['Title'], group=self.group)
            else:
                self.bb.go_back_to_screen_with_title(lang.pack['Preheat']['Edit_Preset']['Add_Material'], group=self.group)

    def save_preset(self):
        #get all the options
        if not self.dual:
            presets = roboprinter.printer_instance._settings.get(['Temp_Preset'])
        else:
            presets = roboprinter.printer_instance._settings.get(['Dual_Temp_Preset'])

        current_screen = roboprinter.robosm.current
        name = next(iter(self.selected_option))


        def save_new_entry():
             #delete old entry
            if not self.dual:
                if self.original_option != None:
                    del presets[self.original_option]
                #save new entry

                presets[name] = self.selected_option[name]

                #save
                roboprinter.printer_instance._settings.set(['Temp_Preset'], presets)
                roboprinter.printer_instance._settings.save()

            else:
                if self.original_option != None:
                    del presets[self.original_option]

                #save new entry
                presets[name] = self.selected_option[name]

                #save
                roboprinter.printer_instance._settings.set(['Dual_Temp_Preset'], presets)
                roboprinter.printer_instance._settings.save()

            #go back to screen
            self.callback('',name)

        def cancel():
            #go back to previous screen
            if self.bb == None:
                roboprinter.robosm.current = current_screen
            else:
                if self.option != None:
                    self.bb.go_back_to_screen_with_title(lang.pack['Preheat']['Edit_Preset']['Title'], group=self.group)
                else:
                    self.bb.go_back_to_screen_with_title(lang.pack['Preheat']['Edit_Preset']['Add_Material'], group=self.group)

        #check for duplicate names


        if name in presets and name != self.original_option and not self.confirm_overwrite:

            #make the modal screen
            body_text = lang.pack['Preheat']['Duplicate']['Body_Text'] + str(name) + lang.pack['Preheat']['Duplicate']['Body_Text1']
            modal_screen = Modal_Question_No_Title(body_text,
                                                   lang.pack['Preheat']['Duplicate']['option1'] ,
                                                   lang.pack['Preheat']['Duplicate']['option2'] ,
                                                   save_new_entry,
                                                   cancel)

            #make screen
            if self.bb == None:
                roboprinter.robosm._generate_backbutton_screen(name='duplicate_error',
                                                               title = lang.pack['Preheat']['Duplicate']['Title'],
                                                               back_destination=current_screen,
                                                               content=modal_screen)
            else:
                self.bb.make_screen(modal_screen,
                                 lang.pack['Preheat']['Duplicate']['Title'],
                                 option_function='no_option',
                                 group=self.group)

        else:
            save_new_entry()


    def delete_preset(self):
        screen = roboprinter.robosm.current
        def delete():
            if not self.dual:
                #get all the options
                presets = roboprinter.printer_instance._settings.get(['Temp_Preset'])

                #delete entry
                name = next(iter(self.selected_option))
                del presets[name]

                #save
                roboprinter.printer_instance._settings.set(['Temp_Preset'], presets)
                roboprinter.printer_instance._settings.save()

                #Info Popup saying that we deleted the preset
                title = lang.pack['Preheat']['Delete']['Deleted']
                ep = Error_Popup(name, title, callback=self.delete_callback)
                ep.show()
            else:
                #get all the options
                presets = roboprinter.printer_instance._settings.get(['Dual_Temp_Preset'])

                #delete entry
                name = next(iter(self.selected_option))
                del presets[name]

                #save
                roboprinter.printer_instance._settings.set(['Dual_Temp_Preset'], presets)
                roboprinter.printer_instance._settings.save()

                #Info Popup saying that we deleted the preset
                title = lang.pack['Preheat']['Delete']['Deleted']
                ep = Error_Popup(name, title, callback=self.delete_callback)
                ep.show()

        def cancel():
            #go back to previous screen
            if self.bb == None:
                roboprinter.robosm.current = screen
            else:
                if self.option != None:
                    self.bb.go_back_to_screen_with_title(lang.pack['Preheat']['Edit_Preset']['Title'], group=self.group)
                else:
                    self.bb.go_back_to_screen_with_title(lang.pack['Preheat']['Edit_Preset']['Add_Material'], group=self.group)

        #make the modal screen
        name = next(iter(self.selected_option))
        body_text = lang.pack['Preheat']['Delete']['Body'] + str(name) + lang.pack['Preheat']['Delete']['Q_Mark']
        modal_screen = Modal_Question_No_Title(body_text,
                                               lang.pack['Preheat']['Delete']['positive'] ,
                                               lang.pack['Preheat']['Delete']['negative'] ,
                                               delete,
                                               cancel)

        #make screen
        if self.bb == None:
            roboprinter.robosm._generate_backbutton_screen(name='delete_preset',
                                                           title = lang.pack['Preheat']['Delete']['Title'] ,
                                                           back_destination=screen,
                                                           content=modal_screen)
        else:
            self.bb.make_screen(modal_screen,
                             lang.pack['Preheat']['Delete']['Title'],
                             option_function='no_option',
                             group=self.group)
