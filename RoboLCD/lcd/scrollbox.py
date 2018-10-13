# -*- coding: utf-8 -*-
# @Author: Matt Pedler
# @Date:   2017-10-25 16:48:06
# @Last Modified by:   Matt Pedler
# @Last Modified time: 2018-01-27 08:33:00
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.properties import ObjectProperty
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.logger import Logger
from kivy.properties import NumericProperty, ObjectProperty, StringProperty,  BooleanProperty
from robo_controls import Temperature_Label
from kivy.clock import Clock
from RoboLCD import roboprinter
from RoboLCD.lcd.Language import lang


class Scroll_Box_Even(BoxLayout):
    """docstring for Scroll_Box_Even"""
    position = 0
    max_pos = 0
    buttons = []
    up_icons = ["Icons/Up-arrow-grey.png", "Icons/Up-arrow-blue.png"]
    down_icons = ["Icons/Down-arrow-grey.png", "Icons/Down-arrow-blue.png"]
    up_icon = ObjectProperty("Icons/Up-arrow-grey.png")
    down_icon = ObjectProperty("Icons/Down-arrow-grey.png")
    def __init__(self, button_array):
        super(Scroll_Box_Even, self).__init__()
        Logger.info("Initializing SBE")
        self.up_event = None
        self.down_event = None
        self.grid = self.ids.content
        self.max_pos = len(button_array) - 4
        self.buttons = button_array
        self.original_scroll_size = self.scroll.size_hint_x
        self.original_scroll_width = self.scroll.width
        if len(self.buttons) <= 4:
            self.scroll.size_hint_x = 0
            self.scroll.width = 0.1
        self.populate_buttons()

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
        if len(self.buttons) <= 4:
            self.scroll.size_hint_x = 0
            self.scroll.width = 0.1
        else:
            self.scroll.size_hint_x = self.original_scroll_size
            self.scroll.width = self.original_scroll_width

    def repopulate_for_new_screen(self):
        self.position = 0
        self.max_pos = len(self.buttons) - 4
        self.populate_buttons()

    def populate_buttons(self):
        content = self.grid

        content.clear_widgets()

        for x in range(0,4):
            if self.position + x < len(self.buttons):
                content.add_widget(self.buttons[self.position + x])
            else:
                content.add_widget(Button(text='', background_color = [0,0,0,1]))

        self.check_for_scroll()

class Scroll_Box_Even_Button(Button):
    button_text = StringProperty("Error")
    generator= ObjectProperty(None)
    arg = ObjectProperty("ERROR")
    def __init__(self, text_button, generator_fuction, arg):
        super(Scroll_Box_Even_Button, self).__init__()
        self.button_text = text_button
        self.generator = generator_fuction
        self.arg = arg

    def cleanup(self):
        Logger.info("Cleaning up SBE button")
        #dereference the generator
        self.generator = "" #set it to a different object that is not our bound method
        #remove self from parent widget
        self.parent.remove_widget(self)



class Scroll_Box_Icons(GridLayout):
    """We should try to not have more than six icons on the screen"""
    cols = NumericProperty(2)
    rows = NumericProperty(3)
    buttons = []
    def __init__(self, button_array, robosm=None, **kwargs):
        super(Scroll_Box_Icons, self).__init__()

        
        #check to see if we need to resize the grid
        length = len(button_array)

        #format the buttons
        if length ==5 or length == 6:
            self.cols = 3
            self.rows = 2
        elif length == 4 or length == 3:
            self.cols = 2
            self.rows = 2
        elif length == 2:
            self.cols = 2
            self.rows = 1
        else:
            self.cols = 1
            self.rows = 1
        #Logger.info("Cols: " + str(self.cols) + " Rows: " + str(self.rows))
        
        self.sm = robosm
        self.grid = self.ids.content
        self.buttons = button_array
        self.populate_buttons()   

    def populate_buttons(self):

        content = self.grid

        content.clear_widgets()
        for but in self.buttons:
            content.add_widget(but)

        length = len(self.buttons)
        if length == 5 or length == 3:
            if self.sm != None:
                tl = Temperature_Label(robosm=self.sm)
                content.add_widget(tl)
            else:
                content.add_widget(Button(text='', background_color = [0,0,0,1],size_hint = [0.0,0.0] ))

class Robo_Icons(Button):
    generator= StringProperty("ROBO_CONTROLS")
    img_source = StringProperty("Icons/Icon_Buttons/Robo_Controls.png")
    icon_name = StringProperty("Robo Controls")
    button_state = ObjectProperty(False)
    callback = ObjectProperty(None)
    def __init__(self, _image_source, _icon_name, _generator_function, callback=None):
        super(Robo_Icons, self).__init__()
        self.generator = _generator_function
        self.img_source = _image_source
        self.original_icon_name = _icon_name
        self.icon_name = _icon_name
        self.button_state = False
        self.callback = callback


    def execute_function(self):
        self.icon_name = lang.pack['Files']['File_Tab']['Loading']
        self.current_screen = roboprinter.robosm.current
        self.first_loop = False
        Clock.schedule_interval(self.Icon_Loading, 0.2)
        
    def Icon_Loading(self, dt):

        #check if this is the first iteration
        if not self.first_loop:
            self.first_loop = True
            self.callback(generator=self.generator, name=self.icon_name)

        if self.current_screen != roboprinter.robosm.current:
            self.icon_name = self.original_icon_name
            #Logger.info("Exiting Loading loop")
            return False
'''
Same as Robo Icons, the kivy file is different though
'''
class Storage_Icons(Button):
    generator= StringProperty("ROBO_CONTROLS")
    img_source = StringProperty("Icons/Icon_Buttons/Robo_Controls.png")
    icon_name = StringProperty("Robo Controls")
    button_state = ObjectProperty(False)
    callback = ObjectProperty(None)
    def __init__(self, _image_source, _icon_name, _generator_function, callback=None):
        super(Storage_Icons, self).__init__()
        self. generator = _generator_function
        self.img_source = _image_source
        self.original_icon_name = _icon_name
        self.icon_name = _icon_name
        self.button_state = False
        self.callback = callback


    def execute_function(self):
        self.icon_name = lang.pack['Files']['File_Tab']['Loading']
        self.current_screen = roboprinter.robosm.current
        self.first_loop = False
        Clock.schedule_interval(self.Icon_Loading, 0.2)
        
    def Icon_Loading(self, dt):

        #check if this is the first iteration
        if not self.first_loop:
            self.first_loop = True
            self.callback(generator=self. generator, name=self.icon_name)

        if self.current_screen != roboprinter.robosm.current:
            self.icon_name = self.original_icon_name
            Logger.info("Exiting Loading loop")
            return False

class Scroll_Box_Icons_Anchor(FloatLayout):
    """We should try to not have more than six icons on the screen"""
    buttons = []
    def __init__(self, button_array):
        super(Scroll_Box_Icons_Anchor, self).__init__()
        self.buttons = button_array
        self.populate_buttons()        

    def populate_buttons(self):

        left = self.ids.left
        left.add_widget(self.buttons[0])

        right = self.ids.right
        right.add_widget(self.buttons[1])

        center = self.ids.center
        center.add_widget(self.buttons[2])
        pass


        


class Robo_Icons_Anchor(Button):
    generator= StringProperty("ROBO_CONTROLS")
    img_source = StringProperty("Icons/Icon_Buttons/Robo_Controls.png")
    icon_name = StringProperty("Robo Controls")
    anchorx = StringProperty("left")
    anchory = StringProperty("center")
    def __init__(self, _image_source, _icon_name, _generator_function, position):
        super(Robo_Icons_Anchor, self).__init__()
        self. generator = _generator_function
        self.img_source = _image_source
        self.icon_name = _icon_name

        acceptable_positions = {'LEFT': {'anchor_x' : 'left', 'anchor_y': 'top'} ,
                                'RIGHT':{'anchor_x' : 'right', 'anchor_y': 'top'},
                                'CENTER':{'anchor_x' : 'center', 'anchor_y': 'bottom'},
                                }

        if position in acceptable_positions:
            self.anchorx = acceptable_positions[position]['anchor_x']
            self.anchory = acceptable_positions[position]['anchor_y']
            Logger.info(self.anchorx + " " + self.anchory)
        else:
            Logger.info(position + " Is not an acceptable position")







        
   



       
        