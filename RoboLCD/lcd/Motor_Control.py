# -*- coding: utf-8 -*-
# @Author: Matt Pedler
# @Date:   2017-10-13 15:38:27
# @Last Modified by:   Matt Pedler
# @Last Modified time: 2018-02-08 11:17:40
from kivy.uix.gridlayout import GridLayout
from kivy.uix.widget import Widget
from kivy.clock import Clock
from kivy.logger import Logger
from kivy.uix.screenmanager import Screen
from kivy.properties import ObjectProperty, StringProperty, BooleanProperty, NumericProperty, ListProperty
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.core.window import Window
from kivy.uix.image import Image
from kivy.graphics import *
from kivy.uix.label import Label
from connection_popup import Mintemp_Warning_Popup, Info_Popup
from manualcontrol import TemperatureControl
from .. import roboprinter
from printer_jog import printer_jog
from kivy.logger import Logger
from pconsole import pconsole
from Language import lang
from common_screens import Button_Group_Observer, OL_Button

class Switchable_Motors(BoxLayout):
    movement_mm = NumericProperty(10)
    current_screen = 0
    def __init__(self):
        super(Switchable_Motors, self).__init__()
        mover = Mover(self)
        observer = Button_Group_Observer()
        self.toggle_mm_xyz = Toggle_mm(self.change_mm, name='xyz', observer=observer)
        self.toggle_mm_ext = Toggle_mm(self.change_mm, name='ext', observer=observer)
        self.xyz_move = XYZ_Movement(mover, self.toggle_mm_xyz)
        printer_type = roboprinter.printer_instance._settings.global_get(['printerProfiles', 'defaultProfile'])
        if printer_type['extruder']['count'] == 1:
            self.extruder = Extruder_Movement(mover, self.toggle_mm_ext)
        elif printer_type['extruder']['count'] > 1:
            self.extruder = Dual_Extruder_Movement(mover, self.toggle_mm_ext)
        self.switch_list = [self.xyz_move, self.extruder]

        self.clear_widgets()
        self.add_widget(self.switch_list[self.current_screen])

    def change_mm(self, mm_value):
        self.movement_mm = mm_value

    def Switch_Layout(self, **kwargs):
        #TODO add a way to switch to a dual extruder screen or a single extruder screen
        self.current_screen += 1

        if self.current_screen == 2:
            self.current_screen = 0

        self.clear_widgets()
        self.add_widget(self.switch_list[self.current_screen])

class MotorControl(GridLayout):
    cols = NumericProperty(5)
    rows = NumericProperty(2)
    padding = ObjectProperty([0,20,0,20])


    def __init__(self, button_list):
        super(MotorControl, self).__init__()
        b_len = len(button_list)

        if b_len == 10:
            self.cols = 5
            self.rows = 2
            self.padding = [0,20,0,20]
        elif b_len == 4:
            self.cols = 2
            self.rows = 2
            self.padding = [175,20,175,20]
        elif b_len == 6:
            self.cols = 3
            self.rows = 2
            self.padding = [90,20,90,20]
        else:
            raise ValueError("Invalid button list for Motor Control, use a list of 10 buttons, 6 Buttons, or 4 buttons")

        self.clear_widgets()
        for button in button_list:
            self.add_widget(button)




class Motor_Control_Operator(Button):
    button_function = ObjectProperty(None)
    button_variable = ObjectProperty('')
    background_normal = StringProperty('')
    control_image = StringProperty('')
    button_text = StringProperty('')

    def __init__(self, button_function, button_variable, background_normal, control_image, button_text):
        super(Motor_Control_Operator, self).__init__()
        self.button_function = button_function
        self.button_variable = button_variable
        self.background_normal = background_normal
        self.control_image = control_image
        self.button_text = button_text


class Toggle_mm(Motor_Control_Operator):
    mms = ListProperty([0.1,1,10,100])
    inx = NumericProperty(2)
    toggle_pic = ['Icons/Manual_Control/increments_4_1.png', 'Icons/Manual_Control/increments_4_2.png', 'Icons/Manual_Control/increments_4_3.png', 'Icons/Manual_Control/increments_4_4.png' ]

    def __init__(self, callback, name='None', observer=None):
        if observer != None:
            self.observer = observer
            self.name = name
            self.observer.register_callback(self.name, self.update_inx)
        else:
            self.observer = observer

        self.callback = callback
        self.button_function = self.button_press
        self.button_variable = self.mms[self.inx]
        self.background_normal = 'Icons/blue_button_style.png'
        self.control_image = self.toggle_pic[self.inx]
        self.button_text = '{}mm'.format(self.mms[self.inx])
        self.callback(self.mms[self.inx])

        super(Toggle_mm, self).__init__(self.button_function, self.button_variable, self.background_normal, self.control_image, self.button_text)


    def toggle_mm(self):
        if self.inx == 3:
            self.inx = 0
        else:
            self.inx += 1
       
        self.control_image = self.toggle_pic[self.inx]
        self.button_text = '{}mm'.format(self.mms[self.inx])

    def update_inx(self, name, inx):
        if int(self.inx) != int(inx):
            self.inx = int(inx)
            self.control_image = self.toggle_pic[self.inx]
            self.button_text = '{}mm'.format(self.mms[self.inx])

    def button_press(self, var):
        self.toggle_mm()
        if self.observer != None:
            self.observer.change_button(self.name, value=self.inx)        
        self.callback(self.mms[self.inx])


class XYZ_Movement(MotorControl):
    

    def __init__(self, move, toggle_mm):
        
        #create Icons
        #button_function, button_variable, background_normal, control_image, button_text
        home = Motor_Control_Operator(move.home, '', 'Icons/blue_button_style.png', 'Icons/Manual_Control/home_icon.png', lang.pack['Motor_Controls']['Home'])
        turn_off_motors = Motor_Control_Operator(move.motors_off, '', 'Icons/Manual_Control/button_red_outline.png', 'Icons/Manual_Control/motors off.png', lang.pack['Motor_Controls']['Motors_Off'])
        raise_the_buildplate = Motor_Control_Operator(move.raise_buildplate, '', 'Icons/blue_button_style.png', 'Icons/Manual_Control/Bed Top.png', lang.pack['Motor_Controls']['Raise_BP'])
        y_plus = Motor_Control_Operator(move.move_pos, 'y', 'Icons/button_pause_blank.png', 'Icons/Manual_Control/Y+_icon.png', lang.pack['Motor_Controls']['Y+'])
        z_minus = Motor_Control_Operator(move.move_neg, 'z', 'Icons/button_pause_blank.png', 'Icons/Manual_Control/Z+_icon.png', lang.pack['Motor_Controls']['Z-'])
        x_minus = Motor_Control_Operator(move.move_neg, 'x', 'Icons/button_pause_blank.png', 'Icons/Manual_Control/X+_icon.png', lang.pack['Motor_Controls']['X-'])
        y_minus = Motor_Control_Operator(move.move_neg, 'y', 'Icons/button_pause_blank.png', 'Icons/Manual_Control/Y-_icon.png', lang.pack['Motor_Controls']['Y-'])
        x_plus = Motor_Control_Operator(move.move_pos, 'x', 'Icons/button_pause_blank.png', 'Icons/Manual_Control/X-_icon.png', lang.pack['Motor_Controls']['X+'])
        z_plus = Motor_Control_Operator(move.move_pos, 'z', 'Icons/button_pause_blank.png', 'Icons/Manual_Control/Z-_icon.png', lang.pack['Motor_Controls']['Z+'])

        #button_list = [toggle_mm, z_plus, y_plus, z_minus, raise_the_buildplate, turn_off_motors, x_minus, y_minus, x_plus, home]
        #button_list = [toggle_mm, x_minus, x_plus, z_minus,  raise_the_buildplate, turn_off_motors, y_plus, y_minus, z_plus,  home]
        button_list = [toggle_mm, y_plus, home, z_minus, raise_the_buildplate, x_minus, y_minus, x_plus, z_plus,  turn_off_motors]

        super(XYZ_Movement, self).__init__(button_list)

    def change_mm(self, mm_value):
        self.movement_mm = mm_value

    

class Temperature_Operator(Button):
    button_function = ObjectProperty(None)
    button_variable = ObjectProperty(None)
    selected_extruder = ObjectProperty('')
    background_normal = StringProperty('')
    button_text = StringProperty('')
    temp_text = StringProperty('')
    heater_title = StringProperty('')

    def __init__(self, button_function, selected_extruder, background_normal):
        super(Temperature_Operator, self).__init__()
        self.button_function = button_function
        self.selected_extruder = selected_extruder
        self.background_normal = background_normal
        self.settings = roboprinter.printer_instance._settings
        self.robo_state = self.get_state()
        self.change_extruder(self.selected_extruder)
        self.heater_not_found = False
        Clock.schedule_interval(self.monitor_selected_temp, 0.2)

    def get_state(self):
        profile = self.settings.global_get(['printerProfiles', 'defaultProfile'])

        if 'extruder' in profile:
            extruder_count = int(profile['extruder']['count'])
        else:
            extruder_count = 1

        #re-enable this code when Dual extrusion is ready for release
        extruder_count = 1

        model = self.settings.get(['Model'])

        return {'model': model,
                'extruder': extruder_count}
        
    
    def change_extruder(self, extruder):
        self.heater_not_found = False
        #get the state of the machine. If we only have one extruder we should just say "Extruder". if more than one "Extruder 1" and 2
        if 'extruder' in self.robo_state and int(self.robo_state['extruder']) == 1:
            acceptable_extruders = {
                'tool0': lang.pack['Temperature_Controls']["Extruder"]
            }
        else:
            acceptable_extruders = {
                'tool0': lang.pack['Temperature_Controls']["Extruder_1"],
                'tool1': lang.pack['Temperature_Controls']["Extruder_2"]
            }
        if extruder in acceptable_extruders:
            self.selected_extruder = extruder
            #button text sets the text of the button
            self.button_text = acceptable_extruders[extruder]
            #heater title sets the title of the next screen
            self.heater_title = acceptable_extruders[extruder]
        else:
            raise ValueError("Use tool0 or tool1")



    def monitor_selected_temp(self, dt):
        cur_temp = self.temperature(self.selected_extruder)
        self.temp_text = str(cur_temp[0]) + lang.pack['Temperature_Controls']['Celsius_with_slash'] + " " + str(cur_temp[1]) + lang.pack['Temperature_Controls']['Celsius_Alone']

        if roboprinter.robosm.current != 'motor_control_screen' and roboprinter.robosm.current != 'tool0' and roboprinter.robosm.current != 'tool1':
            return False

    def temperature(self, extruder):
        temps  = roboprinter.printer_instance._printer.get_current_temperatures()
        current_temperature = [0,0]

        if extruder in temps and 'actual' in temps[extruder] and 'target' in temps[extruder]:
            #check if temperature can be turned to int
            try:
                current_temperature = [int(temps[extruder]['actual']), int(temps[extruder]['target'])]
            except Exception as e:
                if not self.heater_not_found:
                    Info_Popup(lang.pack['Warning']['Heater_Not_Found'], lang.pack['Warning']['Heater_Not_Found_Body']).show()
                    self.heater_not_found = True
            
        else:
            if not self.heater_not_found:
                Info_Popup(lang.pack['Warning']['Heater_Not_Found'], lang.pack['Warning']['Heater_Not_Found_Body']).show()
                self.heater_not_found = True
        
        return current_temperature



class Extruder_Movement(MotorControl):
    def __init__(self, move, toggle_mm):
        #create Icons
        #button_function, button_variable, background_normal, control_image, button_text
        retract = Motor_Control_Operator(move.move_neg, 'e', 'Icons/button_pause_blank.png', 'Icons/Manual_Control/retract_icon.png', lang.pack['Motor_Controls']['Retract'])
        extrude = Motor_Control_Operator(move.move_pos, 'e', 'Icons/button_pause_blank.png', 'Icons/Manual_Control/extrude_icon.png', lang.pack['Motor_Controls']['Extrude'])
        temp_controls = Temperature_Operator(roboprinter.robosm.generate_temperature_controls, 'tool0', 'Icons/blue_button_style.png')

        button_list = [toggle_mm, retract, temp_controls, extrude]

        super(Extruder_Movement, self).__init__(button_list)



class Dual_Extruder_Movement(MotorControl):

    def __init__(self, move, toggle_mm):

        #create Icons
        self.move = move
        tool_observer = Button_Group_Observer()
        #button_function, button_variable, background_normal, control_image, button_text
        retract = Motor_Control_Operator(self.move.move_neg, 'e', 'Icons/button_pause_blank.png', 'Icons/Manual_Control/retract_icon.png', lang.pack['Motor_Controls']['Retract'])
        extrude = Motor_Control_Operator(self.move.move_pos, 'e', 'Icons/button_pause_blank.png', 'Icons/Manual_Control/extrude_icon.png', lang.pack['Motor_Controls']['Extrude'])
        self.temp_controls = Temperature_Operator(roboprinter.robosm.generate_temperature_controls, 'tool0', 'Icons/blue_button_style.png')
        # body_text, image_source, button_function, enabled = True, observer_group = None, **kwargs
        self.change_tool_ext1(0)
        ext_1 = OL_Button(lang.pack['Temperature_Controls']["Extruder_1"], ['Icons/Heater_Icons/Print head 1.png','Icons/Heater_Icons/Print head 1 selected.png'], self.change_tool_ext1, enabled=True, observer_group=tool_observer)
        ext_2 = OL_Button(lang.pack['Temperature_Controls']["Extruder_2"], ['Icons/Heater_Icons/Print head 2.png','Icons/Heater_Icons/Print head 2 selected.png'], self.change_tool_ext2, enabled=False, observer_group=tool_observer)

        button_list = [toggle_mm, retract, ext_1, self.temp_controls, extrude, ext_2]

        super(Dual_Extruder_Movement, self).__init__(button_list)

    #value will come back true or false with no information
    def change_tool_ext1(self, value):
        Logger.info("Selecting tool0")
        self.temp_controls.change_extruder('tool0')
        roboprinter.printer_instance._printer.change_tool('tool0')
        self.move.selected_tool = 'tool0'

    def change_tool_ext2(self, value):
        Logger.info("Selecting tool1")
        self.temp_controls.change_extruder('tool1')
        roboprinter.printer_instance._printer.change_tool('tool1')
        self.move.selected_tool = 'tool1'


    

class Mover():

    def __init__(self, parent):
        self.parent = parent
        self.selected_tool = 'tool0'
        self.warning_shown = False

    def temperature(self):
        temps  = roboprinter.printer_instance._printer.get_current_temperatures()
        current_temperature = 0.00
        if self.selected_tool in temps:
            current_temperature = int(temps[self.selected_tool]['actual'])
        else:
            if not self.warning_shown:
                Info_Popup(lang.pack['Warning']['Heater_Not_Found'], lang.pack['Warning']['Heater_Not_Found_Body']).show()
                self.warning_shown = True
                    
        return current_temperature

    def move_pos(self, axis):
        if axis == 'e' and self.temperature() < 175:
            Info_Popup(lang.pack['Warning']['Mintemp'], str(self.temperature()) + lang.pack['Warning']['Mintemp_Body']).show()
            self.warning_shown = False
        else:
            self._move(axis, self.parent.movement_mm)

    def move_neg(self, axis):
        if axis == 'e' and self.temperature() < 175:
            Info_Popup(lang.pack['Warning']['Mintemp'], str(self.temperature()) + lang.pack['Warning']['Mintemp_Body']).show()
            self.warning_shown = False
        else:
            self._move(axis, -self.parent.movement_mm)

    def _move(self, axis, amnt):
        if axis != 'e':
            jogger = {axis:amnt}
            printer_jog.jog(desired=jogger, speed=1500, relative=True)
        else:
            jogger = {axis:amnt}
            printer_jog.jog(desired=jogger, speed=100, relative=True)

    def home(self, value):
        roboprinter.printer_instance._printer.home(['x', 'y', 'z'])

    def raise_buildplate(self, value):
        roboprinter.printer_instance._printer.commands('G28')
        roboprinter.printer_instance._printer.commands('G90')
        roboprinter.printer_instance._printer.commands('G1 Z20 F3000')

    def motors_off(self, value):            
        roboprinter.printer_instance._printer.commands('M18')




