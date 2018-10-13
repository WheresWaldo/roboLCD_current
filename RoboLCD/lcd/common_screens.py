# -*- coding: utf-8 -*-
# @Author: Matt Pedler
# @Date:   2017-10-27 09:51:01
# @Last Modified by:   Matt Pedler
# @Last Modified time: 2018-01-29 17:33:53
from kivy.logger import Logger
from kivy.properties import ObjectProperty, StringProperty, BooleanProperty, NumericProperty, ListProperty
from .. import roboprinter
from printer_jog import printer_jog
from kivy.clock import Clock
from pconsole import pconsole
from connection_popup import Error_Popup, Warning_Popup
import functools
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.uix.button import Button
from kivy.properties import StringProperty, NumericProperty, ObjectProperty, BooleanProperty
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.uix.togglebutton import ToggleButton
from kivy.core.window import Window
from kivy.uix.vkeyboard import VKeyboard
from Language import lang
from RoboLCD.lcd.session_saver import session_saver

import inspect

import gc
import weakref

#available common screens:

#Wait_Screen
#callback, title, body_text

#Point_Layout
#button_list, body_text

#Modal_Question
#title, body_text, option1_text, option2_text, option1_function, option2_function

#Modal_Question_No_Title
#body_text, option1_text, option2_text, option1_function, option2_function

#Quad_Icon_Layout
#bl1, bl2, body_text

#Button_Screen
#body_text, button_function, button_text = roboprinter.lang.pack['Button_Screen']['Default_Button']

#Picture_Button_Screen
#title_text, body_text,image_source, button_function, button_text = roboprinter.lang.pack['Button_Screen']['Default_Button']

#Picture_Button_Screen_Body
#body_text,image_source, button_function, button_text = roboprinter.lang.pack['Button_Screen']['Default_Button']

#Title_Button_Screen
#title_text, body_text, button_function, button_text = roboprinter.lang.pack['Button_Screen']['Default_Button']

#Temperature_Wait_Screen
#continue_function

#Override_Layout
#button_list, body_text

#OL_Button
#body_text, image_source, button_function, enabled = True, observer_group = None

#Button_Group_Observer
#No arguments

#KeyboardInput
#keyboard_callback = None, default_text = '', name = 'keyboard_screen', title=lang.pack['Files']['Keyboard']['Default_Title'], back_destination=None

#Keypad
#callback, number_length=3,name='keyboard_screen', title=lang.pack['Files']['Keyboard']['Default_Title']

#Auto_Image_Label_Button
#text='', image_icon='', background_normal='', callback=None


#This class is an extension for the wizard BB class. These functions can be taken over by parent classes to
#do whatever they want. The functions are called by the back button and by populating old screens.
class Wizard_Screen_Controls(object):
    _change_screen_actions = {}
    def __init__(self):
        super(Wizard_Screen_Controls, self).__init__()
        #Logger.info("Starting up a Wizard_Screen_Controls instance ID: " + str(id(self)))
        pass

    def cleanup(self):
        Logger.info("############## Cleaning up Wizard_Screen_Controls")
        self.update = '' #dereference update 
        del self.update
        del_list = [] 
        for self_var in self._change_screen_actions:
            del_list.append(self_var)
        for self_var in del_list:
            Logger.info("Deleting " + str(self_var))
            del self._change_screen_actions[self_var]

    @property
    def change_screen_actions(self):
        return self._change_screen_actions

    #for some reason this variable is accessible from every instance of Wizard_Screen_Controls and will fire events from any action in it
    #I'm putting some ID protection on it so it doesn't fire off events at the wrong time. This is a bandaid over a bigger problem that will be investigated
    @change_screen_actions.setter
    def change_screen_actions(self, action):
        if str(id(self)) not in self._change_screen_actions:
            self._change_screen_actions[str(id(self))] = []
        self._change_screen_actions[str(id(self))].append(action)


    def change_screen_event(self):
        #Logger.info("Change Screen Wizard_Screen_Controls instance ID: " + str(id(self)))
        key_instance = str(id(self))
        if key_instance in self._change_screen_actions:
            for event in self._change_screen_actions[key_instance]:
                if callable(event):
                    event()
            #delete all fired events
            Logger.info("Cleaning up callback list for: " + key_instance )

            if key_instance in self._change_screen_actions:
                for item in range(len(self._change_screen_actions[key_instance])):
                    self._change_screen_actions[key_instance][item] = None
                del self._change_screen_actions[key_instance]
            else:
                Logger.info("Key {} does not exist".format(key_instance))

    def update(self):
        #Logger.info("UPDATE Wizard_Screen_Controls instance ID: " + str(id(self)))
        pass

class Wait_Screen(BoxLayout, Wizard_Screen_Controls):
    """Wait Here until the printer stops moving"""
    callback = ObjectProperty(None)
    title = StringProperty("ERROR")
    body_text = StringProperty("ERROR")
    def __init__(self, callback, title, body_text, watch_action=False):
        super(Wait_Screen, self).__init__()
        self.callback = callback
        self.title = title
        self.body_text = body_text
        self.countz = 0
        self.last_countz = 999
        self.counter = 0
        self.changed_screen = False
        self.change_screen_actions = self.wait_screen_back_action
        #this waits 60 seconds before polling for a position. This command is waiting for the M28 command to finish
        #TODO: Make this class monitor the pconsole.busy variable and poll for position, when the printer is ready to recieve commands.
        if watch_action:
            from RoboLCD.lcd.wizards.FTZO.console_watcher import Console_Watcher
            self.cw = Console_Watcher(self.callback_caller)
        else:
            Clock.schedule_once(self.start_check_pos, 50)

    def cleanup(self):
        #call extended classes cleanup
        super(Wait_Screen, self).cleanup()
        self.callback = '' #set callback to nothing
        
        #remove self from parent
        if self.parent:
            self.parent.remove_widget(self)

        #deconstruct self
        #clear self
        del_list = []
        for self_var in self.__dict__:
            del_list.append(self_var)
            self.__dict__[self_var] = ''
        for self_var in del_list:
            Logger.info("Deleting " + str(self_var))
            del self.__dict__[self_var]
        #delete self
        del self

    #this gets kivy back onto the kivy thread to avoid graphical errors
    def callback_caller(self):
        if not self.changed_screen:
            Clock.schedule_once(self.callback, 0.0)
        self.cw.__del__()

    def start_check_pos(self, *args, **kwargs):
        Clock.schedule_interval(self.check_position, 0.2)

    def check_position(self, dt):
        ready = pconsole.busy
        if not ready:
            self.countz = pconsole.get_position()
            if self.countz:

                Logger.info("Count Z: " + str(self.countz[6]) + " last Count Z: " + str(self.last_countz))

                if int(self.countz[6]) == int(self.last_countz):
                    #go to the next screen
                    Logger.info("GO TO NEXT SCREEN! ###########")
                    if not self.changed_screen:
                        self.callback()
                    return False

                self.last_countz = self.countz[6]
        else:
            Logger.info("Pconsole is not ready")

    def wait_screen_back_action(self):
        Logger.info("Wait Screen back button fire")
        self.cw.__del__()
        self.changed_screen = True

#this class is just a screen with some info on it. It is up to the parent class to write an escape from it.
class Info_Screen(BoxLayout, Wizard_Screen_Controls):
    title = StringProperty("")
    body = StringProperty("")

    def __init__(self, title, body):
        super(Info_Screen, self).__init__()
        self.title = title
        self.body = body

class Point_Layout(BoxLayout, Wizard_Screen_Controls):
    body_text = StringProperty("Error")

    def __init__(self, button_list, body_text, **kwargs):
        super(Point_Layout, self).__init__()
        self.body_text =  body_text
        self.button_list = button_list
        self.alter_layout()

    def alter_layout(self):
        grid = self.ids.button_grid

        grid.clear_widgets()

        button_count = len(self.button_list)

        for button in self.button_list:
            grid.add_widget(button)


class Modal_Question(BoxLayout, Wizard_Screen_Controls):
    title = StringProperty("Error")
    body_text = StringProperty("Error")
    option1_text = StringProperty("Error")
    option2_text = StringProperty("Error")
    option1_function = ObjectProperty(None)
    option2_function = ObjectProperty(None)

    def __init__(self, title, body_text, option1_text, option2_text, option1_function, option2_function):
        super(Modal_Question, self).__init__()
        self.title = title
        self.body_text = body_text
        self.option1_text = option1_text
        self.option2_text = option2_text
        self.option1_function = option1_function
        self.option2_function = option2_function

class Modal_Question_No_Title(BoxLayout, Wizard_Screen_Controls):
    body_text = StringProperty("Error")
    option1_text = StringProperty("Error")
    option2_text = StringProperty("Error")
    option1_function = ObjectProperty(None)
    option2_function = ObjectProperty(None)

    def __init__(self, body_text, option1_text, option2_text, option1_function, option2_function):
        super(Modal_Question_No_Title, self).__init__()
        self.body_text = body_text
        self.option1_text = option1_text
        self.option2_text = option2_text
        self.option1_function = option1_function
        self.option2_function = option2_function

class Object_Modal_Question(BoxLayout, Wizard_Screen_Controls):
    custom_object = ObjectProperty(None)
    option1_text = StringProperty("Error")
    option2_text = StringProperty("Error")
    option1_function = ObjectProperty(None)
    option2_function = ObjectProperty(None)

    def __init__(self, custom_object, option1_text, option2_text, option1_function, option2_function):
        super(Object_Modal_Question, self).__init__()
        self.custom_object = custom_object
        self.option1_text = option1_text
        self.option2_text = option2_text
        self.option1_function = option1_function
        self.option2_function = option2_function

        if self.custom_object != None:
            self.ids.custom_object_box.add_widget(self.custom_object)
        else:
            raise ValueError("Custom Object needs to be something else besides None.")

    def cleanup(self):
        Logger.info("Cleaning up Object_Modal_Question")
        super(Object_Modal_Question, self).cleanup()

        #remove self from parent widget
        if self.parent:
            self.parent.remove_widget(self)

        #delete bound objects
        self.custom_object = ''
        self.option1_function = ''
        self.option2_function = ''

        #dereference self    
        del_list = []
        for self_var in self.__dict__:
            del_list.append(self_var)
            self.__dict__[self_var] = '' #set variables to nothing.
        for self_var in del_list:
            Logger.info("Deleting " + str(self_var))
            del self.__dict__[self_var]

        # #Tell Self to print out any remaining referrers 
        # Logger.info("---> Printing referrers of Object_Modal_Question")
        # gc.collect()
        # for referer in gc.get_referrers(self):
        #     Logger.info(referer)
        # Logger.info("---> Done printing referrers of Object_Modal_Question")

        #delete self.
        del self




class Quad_Icon_Layout(BoxLayout, Wizard_Screen_Controls):
    body_text = StringProperty("Error")

    def __init__(self, bl1, bl2, body_text, **kwargs):
        super(Quad_Icon_Layout, self).__init__()
        self.body_text =  body_text
        self.bl1 = bl1
        self.bl2 = bl2
        self.alter_layout()

    def alter_layout(self):
        grid = self.ids.button_grid

        grid.clear_widgets()


        #make a 2x2 grid
        for button in self.bl1:
            grid.add_widget(button)

        for button in self.bl2:
            grid.add_widget(button)

class Button_Screen(BoxLayout, Wizard_Screen_Controls):
    body_text = StringProperty("Error")
    button_function = ObjectProperty(None)
    button_text = StringProperty("OK")

    def __init__(self, body_text, button_function, button_text = roboprinter.lang.pack['Button_Screen']['Default_Button'], **kwargs):
        super(Button_Screen, self).__init__()
        self.body_text = body_text
        self.button_function = button_function
        self.button_text = button_text

    def cleanup(self):
        Logger.info("Cleaning up Button_Screen")
        #call to extended cleanup functions
        super(Button_Screen, self).cleanup()

        #dereference bound function
        self.button_function = ''

        #remove self from parent
        if self.parent:
            self.parent.remove_widget(self)

class Object_Button_Screen(BoxLayout, Wizard_Screen_Controls):
    custom_object = ObjectProperty(None)
    button_function = ObjectProperty(None)
    button_text = StringProperty("OK")

    def __init__(self, custom_object, button_function, button_text = roboprinter.lang.pack['Button_Screen']['Default_Button'], **kwargs):
        super(Object_Button_Screen, self).__init__()
        self.custom_object = custom_object
        self.button_function = button_function
        self.button_text = button_text

        if self.custom_object != None:
            self.ids.custom_object_box.add_widget(self.custom_object)
        else:
            raise ValueError("Custom Object needs to be something else besides None.")

class Image_on_Button_Screen(BoxLayout, Wizard_Screen_Controls):
    body_text = StringProperty("Error")
    button_function = ObjectProperty(None)
    button_image = StringProperty("Icons/Printer Status/blank-warning.png")
    button_text = StringProperty("OK")

    def __init__(self, body_text, button_function, button_image, button_text = roboprinter.lang.pack['Button_Screen']['Default_Button'], **kwargs):
        super(Image_on_Button_Screen, self).__init__()
        self.body_text = body_text
        self.button_function = button_function
        self.button_image = button_image
        self.button_text = button_text


class Picture_Button_Screen(BoxLayout, Wizard_Screen_Controls):
    title_text = StringProperty("Error")
    body_text = StringProperty("Error")
    image_source = StringProperty("Icons/Slicer wizard icons/button bkg active.png")
    button_function = ObjectProperty(None)
    button_text = StringProperty("OK")

    def __init__(self, title_text, body_text,image_source, button_function, button_text = roboprinter.lang.pack['Button_Screen']['Default_Button'], **kwargs):
        super(Picture_Button_Screen, self).__init__()
        self.title_text = title_text
        self.body_text = body_text
        self.image_source = image_source
        self.button_function = button_function
        self.button_text = button_text

    def update_image(self, new_source):
        self.image_source = new_source

    def cleanup(self):
        super(Picture_Button_Screen, self).cleanup()
        Logger.info("Cleaning up Picture_Button_Screen")
        self.button_function = '' #set button function to nothing


class Title_Picture_Image_on_Button_Screen(BoxLayout, Wizard_Screen_Controls):
    title_text = StringProperty("Error")
    body_text = StringProperty("Error")
    image_source = StringProperty("Icons/Slicer wizard icons/button bkg active.png")
    button_function = ObjectProperty(None)
    button_image = StringProperty("Icons/Printer Status/blank-warning.png")
    button_text = StringProperty("OK")

    def __init__(self, title_text, body_text,image_source, button_function, button_image, button_text = roboprinter.lang.pack['Button_Screen']['Default_Button'], **kwargs):
        super(Title_Picture_Image_on_Button_Screen, self).__init__()
        self.title_text = title_text
        self.body_text = body_text
        self.image_source = image_source
        self.button_function = button_function
        self.button_image = button_image
        self.button_text = button_text

class Picture_Image_on_Button_Screen(BoxLayout, Wizard_Screen_Controls):
    title_text = StringProperty("Error")
    body_text = StringProperty("Error")
    image_source = StringProperty("Icons/Slicer wizard icons/button bkg active.png")
    button_function = ObjectProperty(None)
    button_text = StringProperty("OK")
    button_image = StringProperty("Icons/Printer Status/blank-warning.png")

    def __init__(self, body_text,image_source, button_function, button_image, button_text = roboprinter.lang.pack['Button_Screen']['Default_Button'], **kwargs):
        super(Picture_Image_on_Button_Screen, self).__init__()
        self.body_text = body_text
        self.image_source = image_source
        self.button_function = button_function
        self.button_image = button_image
        self.button_text = button_text

    def cleanup(self):
        super(Picture_Image_on_Button_Screen, self).cleanup()

        #dereference function
        self.button_function = ''

class Picture_Button_Screen_Body(BoxLayout, Wizard_Screen_Controls):
    body_text = StringProperty("Error")
    image_source = StringProperty("Icons/Slicer wizard icons/button bkg active.png")
    button_function = ObjectProperty(None)
    button_text = StringProperty("OK")

    def __init__(self, body_text,image_source, button_function, button_text = roboprinter.lang.pack['Button_Screen']['Default_Button'], **kwargs):
        super(Picture_Button_Screen_Body, self).__init__()
        self.body_text = body_text
        self.image_source = image_source
        self.button_function = button_function
        self.button_text = button_text

class Title_Button_Screen(BoxLayout, Wizard_Screen_Controls):
    title_text = StringProperty("Error")
    body_text = StringProperty("Error")
    button_function = ObjectProperty(None)
    button_text = StringProperty("OK")

    def __init__(self, title_text, body_text, button_function, button_text = roboprinter.lang.pack['Button_Screen']['Default_Button'], **kwargs):
        super(Title_Button_Screen, self).__init__()
        self.title_text = title_text
        self.body_text = body_text
        self.button_function = button_function
        self.button_text = button_text


class Picture_Instructions(BoxLayout, Wizard_Screen_Controls):

    def __init__(self):
        super(Picture_Instructions, self).__init__()
        pass


class Temperature_Wait_Screen(BoxLayout, Wizard_Screen_Controls, object):
    continue_function = ObjectProperty(None)
    body_text = StringProperty(lang.pack['Filament_Wizard']['Auto_Next'])
    extruder_temp = NumericProperty(0)
    max_temp = NumericProperty(190)
    _tool_select = 'tool0'
    title = StringProperty(lang.pack['Filament_Wizard']['Prep_Ext1'])


    def __init__(self, continue_function, tool_select='tool0', **kwargs):
        super(Temperature_Wait_Screen, self).__init__()
        self.continue_function = continue_function
        self.changed_screen = False
        self.change_screen_actions = self.change_screen_event_action

        #check for valid tool select
        acceptable_tools = ['tool0', 'tool1']
        if tool_select in acceptable_tools:
            Logger.info("Changing tool!")
            self.tool_select = tool_select
        else:
            raise ValueError("Invalid tool selected. There is no tool named: " + str(tool_select))

        self.clock_obj = Clock.schedule_interval(self.wait_for_temp, 0.2)

    def callback_caller(self):
        Logger.info("Canceling clock and moving on")
        self.clock_obj.cancel()
        self.continue_function()

    @property
    def tool_select(self):
        return self._tool_select
    @tool_select.setter
    def tool_select(self, update):
        self._tool_select = update
        self.on_tool_select(self._tool_select)

    def get_state(self):
        Logger.info("Finding State")
        profile = roboprinter.printer_instance._settings.global_get(['printerProfiles', 'defaultProfile'])

        if 'extruder' in profile:
            extruder_count = int(profile['extruder']['count'])
        else:
            extruder_count = 1

        model = roboprinter.printer_instance._settings.get(['Model'])

        return {'model': model,
                'extruder': extruder_count}


    def on_tool_select(self, tool_select):
        state = self.get_state()

        if int(state['extruder']) > 1:
            Logger.info("Found " + str(state['extruder']) + " Extruders")
            tools = {
                    'tool0': lang.pack['Filament_Wizard']['Prep_Ext1'],
                    'tool1': lang.pack['Filament_Wizard']['Prep_Ext2']
            }

            if tool_select in tools:
                self.title = tools[tool_select]
            else:
                raise ValueError("Invalid tool selected. There is no tool named: " + str(tool_select))
        else:
            Logger.info("Found " + str(state['extruder']) + " Extruders")
            self.title = lang.pack['Filament_Wizard']['Prep_Single']

    #Small Callback for another class to hook into
    def change_screen_event_action(self):
        Logger.info("Change Screen Event Called")
        self.clock_obj.cancel()
        self.changed_screen = True

    def wait_for_temp(self, dt):
        temps = roboprinter.printer_instance._printer.get_current_temperatures()
        #get current temperature
        if self.tool_select in temps:
            if 'actual' in temps[self.tool_select] and 'target' in temps[self.tool_select]:
                temp = temps[self.tool_select]['actual']
                max_temp = temps[self.tool_select]['target']

                if temp == None or max_temp == None:
                    temp = 0
                    max_temp = 0

                self.extruder_temp = temp
                self.max_temp = max_temp

                if max_temp > 5 and temp >= max_temp:
                    #go to the next screen
                    self.callback_caller()
                    return False

                #check for a screen change
                if self.changed_screen:
                    Logger.info("Cancelled because of a change screen event")
                    self.clock_obj.cancel()
                    return False

            else:
                Logger.info("Not found in temps: " + self.tool_select)
                import json
                Logger.info("Temps:" + str(json.dumps(temps, indent=4)))
        else:
            Logger.info("Not found in temps: " + self.tool_select)
            import json
            Logger.info("Temps:" + str(json.dumps(temps, indent=4)))

class Override_Layout(BoxLayout, Wizard_Screen_Controls):
    body_text = StringProperty("Error")
    button_padding = ObjectProperty([0,0,0,0])

    def __init__(self, button_list, body_text, **kwargs):
        super(Override_Layout, self).__init__()
        self.body_text =  body_text
        self.button_list = button_list
        self.alter_layout()

    def alter_layout(self):
        grid = self.ids.button_grid

        grid.clear_widgets()

        button_count = len(self.button_list)
        if button_count == 2:
            #make a 2 grid
            self.button_padding = [200,0,200,35]
            for button in self.button_list:
                grid.add_widget(button)

        elif button_count == 4:
            #make a 4 grid
            self.button_padding = [15,0,15,35]
            for button in self.button_list:
                grid.add_widget(button)

        elif button_count == 3:
            #make a 3 grid
            self.button_padding = [100,0,100,35]
            for button in self.button_list:
                grid.add_widget(button)
        else:
            #Throw an error because there's only supposed to be 2 and 4
            pass




class OL_Button(Button):
    button_text = StringProperty("Error")
    pic_source = StringProperty("Icons/Slicer wizard icons/low.png")
    pic_options = ListProperty(['',''])
    button_background = ObjectProperty("Icons/Keyboard/keyboard_button.png")
    button_bg = ObjectProperty(["Icons/Slicer wizard icons/button bkg inactive.png", "Icons/Slicer wizard icons/button bkg active.png"])
    bg_count = NumericProperty(0)
    button_function = ObjectProperty(None)
    def __init__(self, body_text, image_source, button_function, enabled = True, observer_group = None, **kwargs):
        super(OL_Button, self).__init__()
        self.button_text = body_text
        if type(image_source) == list:
            if len(image_source) == 2:
                self.pic_options = image_source
                self.pic_source = self.pic_options[0]
            else:
                raise ValueError("Image source can only be two pictures at max.")
        else:
            self.pic_source = image_source
            self.pic_options = [image_source, image_source]

        self.button_function = button_function

        #add self to observer group
        self.observer_group = observer_group
        if self.observer_group != None:
            self.observer_group.register_callback(self.button_text, self.toggle_bg)
            if enabled:
                self.observer_group.change_button(self.button_text)
        else:
            if enabled:
                #show blue or grey for enabled or disables
                self.change_state(enabled)


    def change_bg(self):
        if self.observer_group != None:
            if self.observer_group.active_button != self.button_text:
                if self.bg_count == 1 :
                    self.bg_count = 0
                else:
                    self.bg_count += 1

                if self.bg_count == 1:
                    self.observer_group.change_button(self.button_text)

                #self.change_state(self.bg_count)
        else:
            if self.bg_count == 1:
                self.bg_count = 0
            else:
                self.bg_count += 1
            self.change_state(self.bg_count)

    def toggle_bg(self, name):
        if str(name) == str(self.button_text):
            self.button_function(True)
            self.bg_count = 1
        else:
            self.bg_count = 0
        self.button_background = self.button_bg[self.bg_count]
        if self.pic_options != None:
            self.pic_source = self.pic_options[self.bg_count]

    def change_state(self, state):
        if state:
            self.bg_count = 1
            self.button_function(True)
        else:
            self.bg_count = 0
            self.button_function(False)
        self.button_background = self.button_bg[self.bg_count]
        if self.pic_options != None:
            self.pic_source = self.pic_options[self.bg_count]


class Button_Group_Observer():
    def __init__(self):
        self._observers = {}
        self.active_button = 'none'

    def register_callback(self, name, callback):
        self._observers[name] = callback

    def change_button(self, name, value=None):
        self.active_button = name
        if name in self._observers:
            for observer in self._observers:
                if value != None:
                    self._observers[observer](name, value)
                else:
                    self._observers[observer](name)


class KeyboardInput(FloatLayout, Wizard_Screen_Controls):
    kbContainer = ObjectProperty()
    keyboard_callback = ObjectProperty(None)
    default_text = StringProperty('')

    def __init__(self, keyboard_callback = None,
                       default_text = '',
                       name = 'keyboard_screen',
                       title=lang.pack['Files']['Keyboard']['Default_Title'],
                       back_destination=None,
                       back_button=None,
                       group=None,
                       **kwargs):
        super(KeyboardInput, self).__init__(**kwargs)
        self.default_text = default_text
        self.back_destination = back_destination
        self.first_press = False
        self.bb=back_button
        self.group=group
        self.title = title
        if self.back_destination == None:
            self.back_destination = roboprinter.robo_screen()

        if self.bb == None:
            roboprinter.back_screen(name=name,
                                    title=title,
                                    back_destination=self.back_destination,
                                    content=self)
        else:
            self.bb.make_screen(self,
                             title,
                             option_function='no_option',
                             group=self.group)
        self.current_screen = roboprinter.robo_screen()
        self._keyboard = None
        self._set_keyboard('keyboards/abc.json')
        if keyboard_callback != None:
            self.keyboard_callback = keyboard_callback

        self.keyboard_watch = Clock.schedule_interval(self.monitor_screen_change, 0.2)

    def close_screen(self):
        if self._keyboard:
            Window.release_all_keyboards()
            roboprinter.robosm.current = self.back_destination
        self.keyboard_watch.cancel()

    def monitor_screen_change(self,dt):

        if self.bb == None:
            if self.current_screen != roboprinter.robo_screen():
                if self._keyboard:
                    Window.release_all_keyboards()

                return False
        else:
            if self.bb.title != self.title:
                if self._keyboard:
                    Window.release_all_keyboards()

                return False

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


class Keypad(BoxLayout, Wizard_Screen_Controls):
    input_temp = StringProperty('0')
    desired_temp = 0

    def __init__(self, callback, number_length=3,name='keyboard_screen', title=lang.pack['Files']['Keyboard']['Default_Title'], back_button=None, group=None,**kwargs):
        super(Keypad, self).__init__()
        self.back_destination = roboprinter.robo_screen()
        self.callback = callback
        self.number_length = number_length
        self.bb = back_button
        self.group = group

        if self.bb == None:
            roboprinter.back_screen(name=name,
                                    title=title,
                                    back_destination=self.back_destination,
                                    content=self)
        else:
            self.bb.make_screen(self,
                             title,
                             option_function='no_option',
                             group=self.group)


    def add_number(self, number):
        Logger.info(str(number) + " Hit")

        text = str(self.desired_temp)

        if len(text) < self.number_length:

            self.desired_temp = self.desired_temp * 10 + number
            self.input_temp = str(self.desired_temp)

    def delete_number(self):
        self.desired_temp = int(self.desired_temp / 10)
        self.input_temp = str(self.desired_temp)

    def set_number(self):
        self.callback(self.input_temp)
        roboprinter.robosm.current = self.back_destination




class Auto_Image_Label_Button(Button):
    background_normal = StringProperty("Icons/blue_button_style.png")
    image_icon = StringProperty("Icons/Printer Status/pause_button_icon.png")
    button_text = StringProperty("Error")
    callback = ObjectProperty(None)

    def __init__(self, text='', image_icon='', background_normal='', callback=None, **kwargs):
        self.button_text = text
        self.image_icon = image_icon
        self.background_normal = background_normal
        self.callback = callback
        self.kwargs = kwargs
        super(Auto_Image_Label_Button, self).__init__()

    def button_press(self):
        if self.callback != None:
            self.callback(**self.kwargs)

#This class will show an option between Ext1 Ext2 or Both
class Extruder_Selector(Override_Layout, Wizard_Screen_Controls):
    """docstring for Extruder_Selector"""
    end_point = ObjectProperty(None)
    button_list = ObjectProperty([])
    current_selection = StringProperty("EXT1")
    def __init__(self, end_point, make_screen=None, only_extruder=False, selected_tool='EXT1', **kwargs):
        #define end point
        self.end_point = end_point
        self.make_screen = make_screen
        self.only_extruder = only_extruder
        self.selected_tool = selected_tool
        #generate screen options
        self.generate_options()

        #make body
        self.body = lang.pack['Extruder_Select']['Body']

        super(Extruder_Selector, self).__init__(self.button_list, self.body)

    def show_screen(self):
        back_destination = roboprinter.robosm.current

        title = lang.pack['Extruder_Select']['Title']

        #make the screen
        if self.make_screen == None:
            roboprinter.back_screen(name = 'select_extruder',
                                    title = title,
                                    back_destination=back_destination,
                                    content=self,
                                    cta = self.return_to_end_point,
                                    icon = "Icons/Slicer wizard icons/next.png")
        else:
            self.make_screen(self,
                             title,
                             option_function=self.return_to_end_point,
                             option_icon="Icons/Slicer wizard icons/next.png")


    def generate_options(self):
        #make an observer for the different buttons
        observer = Button_Group_Observer()

        #make buttons for the user to choose between

        ext1_selected = False
        ext2_selected = False
        both_selected = False

        if self.selected_tool == 'EXT1':
            ext1_selected = True
        elif self.selected_tool == 'EXT2':
            ext2_selected = True
        elif self.selected_tool == 'BOTH':
            both_selected = True
        else:
            ext1_selected = True #defaults to have the first options selected

        #Ext1
        ext_1 = OL_Button(lang.pack['Temperature_Controls']["Extruder_1"],
                                    ['Icons/Heater_Icons/Print head 1.png','Icons/Heater_Icons/Print head 1 selected.png'],
                                    self.select_ext1,
                                    enabled=ext1_selected,
                                    observer_group=observer)

        ext_2 = OL_Button(lang.pack['Temperature_Controls']["Extruder_2"],
                                    ['Icons/Heater_Icons/Print head 2.png','Icons/Heater_Icons/Print head 2 selected.png'],
                                    self.select_ext2,
                                    enabled=ext2_selected,
                                    observer_group=observer)

        both = OL_Button(lang.pack['Extruder_Select']['Both'],
                         'Icons/Heater_Icons/Print head both.png',
                         self.select_both,
                         enabled=both_selected,
                         observer_group=observer)

        #Choose between having three options and having two options
        if not self.only_extruder:
            self.button_list = [ext_1, ext_2, both]
        else:
            self.button_list = [ext_1, ext_2]

        return

    def select_ext1(self, *args, **kwargs):
        self.current_selection = "EXT1"
    def select_ext2(self, *args, **kwargs):
        self.current_selection = "EXT2"
    def select_both(self, *args, **kwargs):
        self.current_selection = 'BOTH'

    def return_to_end_point(self):
        self.end_point(self.current_selection)

#This class will show all available heaters to choose from
class Heater_Selector(Override_Layout, Wizard_Screen_Controls):
    """docstring for Extruder_Selector"""
    end_point = ObjectProperty(None)
    button_list = ObjectProperty([])
    current_selection = StringProperty("EXT1")
    def __init__(self, end_point, make_screen=None, only_extruder=False, selected_tool='EXT1', **kwargs):
        #define end point
        self.end_point = end_point
        self.make_screen = make_screen
        self.only_extruder = only_extruder
        self.selected_tool = selected_tool
        #generate screen options
        self.settings = roboprinter.printer_instance._settings
        self.generate_options()


        #make body
        self.body = lang.pack['Heater_Select']['Body']

        super(Heater_Selector, self).__init__(self.button_list, self.body)

    def cleanup(self):
        #cleanup inherited classes
        super(Heater_Selector, self).cleanup()

        #cleanup given bound objects
        self.end_point = ''
        self.make_screen = ''

        #dereference self    
        del_list = []
        for self_var in self.__dict__:
            del_list.append(self_var)
            self.__dict__[self_var] = '' #set variables to nothing.
        for self_var in del_list:
            Logger.info("Deleting " + str(self_var))
            del self.__dict__[self_var]

        #Tell Self to print out any remaining referrers 
        Logger.info("---> Printing referrers of Heater_Selector")
        gc.collect()
        for referer in gc.get_referrers(self):
            Logger.info(referer)
        Logger.info("---> Done printing referrers of Heater_Selector")

        del self


    def show_screen(self):
        back_destination = roboprinter.robosm.current

        title = lang.pack['Heater_Select']['Title']

        #make the screen
        if self.make_screen == None:
            roboprinter.back_screen(name = 'select_extruder',
                                    title = title,
                                    back_destination=back_destination,
                                    content=self,
                                    cta = self.return_to_end_point,
                                    icon = "Icons/Slicer wizard icons/next.png")
        else:
            self.make_screen(self,
                             title,
                             option_function=self.return_to_end_point,
                             option_icon="Icons/Slicer wizard icons/next.png")

    def get_state(self):
        profile = self.settings.global_get(['printerProfiles', 'defaultProfile'])

        if 'extruder' in profile:
            extruder_count = int(profile['extruder']['count'])
        else:
            extruder_count = 1

        model = self.settings.get(['Model'])

        return {'model': model,
                'extruder': extruder_count}


    def generate_options(self):

        #get available heaters
        state = self.get_state()
        #make an observer for the different buttons
        observer = Button_Group_Observer()

        #make buttons for the user to choose between
        ext1_selected = False
        ext2_selected = False
        bed_selected = False

        if self.selected_tool == 'EXT1':
            ext1_selected = True
        elif self.selected_tool == 'EXT2':
            ext2_selected = True
        elif self.selected_tool == 'BED':
            bed_selected = True
        else:
            ext1_selected = True #defaults to have the first options selected

        #Ext1
        ext_1 = OL_Button(lang.pack['Temperature_Controls']["Extruder_1"],
                                    ['Icons/Heater_Icons/Print head 1.png','Icons/Heater_Icons/Print head 1 selected.png'],
                                    self.select_ext1,
                                    enabled=ext1_selected,
                                    observer_group=observer)

        ext_2 = OL_Button(lang.pack['Temperature_Controls']["Extruder_2"],
                                    ['Icons/Heater_Icons/Print head 2.png','Icons/Heater_Icons/Print head 2 selected.png'],
                                    self.select_ext2,
                                    enabled=ext2_selected,
                                    observer_group=observer)

        bed = OL_Button(lang.pack['Heater_Select']['Bed'],
                         ['Icons/Heater_Icons/Bed.png', 'Icons/Heater_Icons/Bed selected.png'],
                         self.select_bed,
                         enabled=bed_selected,
                         observer_group=observer)

        #Choose between having three options and having two options
        self.button_list = []
        if self.only_extruder:
            #parse out available heaters
            if int(state['extruder']) > 1:
                self.button_list.append(ext_1)
                self.button_list.append(ext_2)
            else:
                #if you only want extruders and there's only one, then return the only extruder
                self.select_ext1()
                self.return_to_end_point()

        else:
            if int(state['extruder']) > 1:
                self.button_list.append(ext_1)
                self.button_list.append(ext_2)
            else:
                ext_1 = OL_Button(lang.pack['Temperature_Controls']["Extruder"],
                                    ['Icons/Heater_Icons/Print head 1.png','Icons/Heater_Icons/Print head 1 selected.png'],
                                    self.select_ext1,
                                    enabled=ext1_selected,
                                    observer_group=observer)

                self.button_list.append(ext_1)

            if state['model'] == "Robo R2":
                self.button_list.append(bed)

        if len(self.button_list) == 0:
            raise ValueError("No available heaters " + str(temps))


        return

    def select_ext1(self, *args, **kwargs):
        self.current_selection = "EXT1"
    def select_ext2(self, *args, **kwargs):
        self.current_selection = "EXT2"
    def select_bed(self, *args, **kwargs):
        self.current_selection = 'BED'

    def return_to_end_point(self):
        if callable(self.end_point):
            self.end_point(self.current_selection)
        else:
            Logger.info("End point is no longer callable")
