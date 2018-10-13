# -*- coding: utf-8 -*-
# @Author: Matt Pedler
# @Date:   2017-09-27 17:53:43
# @Last Modified by:   Matt Pedler
# @Last Modified time: 2018-01-09 11:57:31
# coding=utf-8
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.tabbedpanel import TabbedPanelHeader
from kivy.properties import NumericProperty, StringProperty, ObjectProperty, VariableListProperty
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.logger import Logger
from kivy.clock import Clock
from kivy.uix.modalview import ModalView
from RoboLCD import roboprinter
from connection_popup import Zoffset_Warning_Popup, Update_Warning_Popup
import math
import subprocess
from multiprocessing import Process
from pconsole import pconsole
from RoboLCD.lcd.update_system.old_system.updater import UpdateScreen
from session_saver import session_saver
import time
import traceback
from functools import partial
from scrollbox import Scroll_Box_Even, Scroll_Box_Icons, Robo_Icons
from common_screens import Auto_Image_Label_Button

#errors and warnings
from errors_and_warnings import Error_Detection


class PrinterStatusTab(TabbedPanelHeader):
    """
    Represents the Printer Status tab header and dynamic content
    """
    pass


class PrinterStatusContent(BoxLayout):
    """
    """
    filename = StringProperty("")
    status = StringProperty("None")
    extruder_one_temp = NumericProperty(0)
    extruder_one_max_temp = NumericProperty(200)
    extruder_two_max_temp = NumericProperty(200)
    extruder_two_temp = NumericProperty(0)
    bed_max_temp = NumericProperty(200)
    bed_temp = NumericProperty(0)
    progress = StringProperty('')
    progress_number = NumericProperty(0)
    startup = False 
    safety_counter = 0
    update_lock = False
    etr = StringProperty("Error")
    te = StringProperty("Error")
    etr_start_time = -999
    te_start_time = -999
    first_round = True
    progress_width = NumericProperty(200)
    printing = True

    tae_x = NumericProperty(0)
    tae_y = NumericProperty(0)
    triangle_y = -150    
    grey_color = [0.50390625,0.49609375,0.49609375,1]
    black_color = [0.0,0.0,0.0,1.0]
    white_color = [1,1,1,1]
    green_color = [0,1,0,1]
    error_color = VariableListProperty([0.0,0.0,0.0,1.0], length=4)
    temp_color = VariableListProperty([0.0,0.0,0.0,1.0], length=4)

    

    #temp and error message icons
    temp_icon = StringProperty('Icons/Icon_Buttons/Temperature.png')
    error_icon = StringProperty('Icons/failure_icon.png')


    
    

    def __init__(self,*args,**kwargs):
        super(PrinterStatusContent, self).__init__(*args,**kwargs)  
        #get the model
        self.model = roboprinter.printer_instance._settings.get(['Model'])   

        self.splash_event = Clock.schedule_interval(self.turn_off_splash, .1)
        self.extruder = Temp_Control_Button()
        self.manual = Motor_Control_Button()
        Clock.schedule_interval(self.monitor_errors, 0.2)
        self.update_lock = False
        Clock.schedule_interval(self.safety, 1)
        Clock.schedule_interval(self.update, 0.2)   

        #add the move tools function to a global space
        session_saver.saved['Move_Tools'] = self.move_tools_to    


    def move_tools_to(self, content_space):
        
        if content_space == "ERROR":
            if self.model == "Robo R2":
                self.tae_x = -800
            else:
                self.tae_x = -720
            
            self.error_color = self.grey_color
            self.temp_color = self.black_color
            self.canvas.ask_update()
        elif content_space == "TEMP":
            self.tae_x = 0
            
            self.error_color = self.black_color
            self.temp_color = self.grey_color
            self.canvas.ask_update()

    def add_error_box(self):


        #add the error container
        error_detection = Error_Detection()
        error_content = self.ids.error_box
        error_content.clear_widgets()
        error_content.add_widget(error_detection)

    def update(self, dt):

        current_data = roboprinter.printer_instance._printer.get_current_data()
        is_printing = current_data['state']['flags']['printing']
        is_paused = current_data['state']['flags']['paused']

        if (is_printing or is_paused) and not self.printing:
            self.printing = True
            self.start_print(0)
            self.move_tools_to("TEMP")
            #Add Start and pause buttons
            extruder_buttons = self.ids.status_buttons   
            extruder_buttons.clear_widgets() 
            extruder_buttons.add_widget(StartPauseButton())
            extruder_buttons.add_widget(CancelButton())
        elif not is_printing and not is_paused and self.printing:
            self.printing = False
            self.end_print(0)
            self.move_tools_to("ERROR")  

            #Add Motor Controls and Temp Controls
            extruder_buttons = self.ids.status_buttons   
            extruder_buttons.clear_widgets() 
            self.extruder = Temp_Control_Button()
            self.manual = Motor_Control_Button()
            extruder_buttons.add_widget(self.extruder)
            extruder_buttons.add_widget(self.manual)            
        if self.first_round:
            self.first_round = False
            self.add_error_box()

        #Monitor Temperature
        if self.is_anything_hot():
            #swap icons
            self.temp_icon = "Icons/Printer Status/red temp icon.png"
        else:
            self.temp_icon = "Icons/Icon_Buttons/Temperature.png"


    def is_anything_hot(self):
        temp1 = self.grab_target_and_actual('tool0')
        temp2 = self.grab_target_and_actual('tool1')
        bed = self.grab_target_and_actual('bed')

        temps = [temp1['target'], temp2['target'], bed['target']]

        for temp in temps:
            if temp > 0.0:
                return True

        return False


    def start_print(self, dt):
        try:
            #make new object for the printer
            print_screen = Print_Screen()
    
            #clear widgets from the screen
            content_space = self.ids.printer_content
            content_space.clear_widgets()
            content_space.clear_widgets()
    
            #add the print screen
            content_space.add_widget(print_screen)
        except Exception as e:
            Logger.info("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! "+ str(e))
            traceback.print_exc()
        
        

    def end_print(self, dt):
        try:
            #make new object for the printer
            idle_screen = Idle_Screen()       

            #clear widgets from the screen
            content_space = self.ids.printer_content
            content_space.clear_widgets()
            content_space.clear_widgets()

            #add Idle Screen
            content_space.add_widget(idle_screen)
    
        except AttributeError as e:
            Logger.info("Error in End Print")
            Clock.schedule_once(self.end_print, 1)
            Logger.info("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! "+ str(e))
            traceback.print_exc()

    def monitor_errors(self, dt):
        #monitor for errors
        if 'current_error' in session_saver.saved:
            error = session_saver.saved['current_error']

            if error == 'MAINBOARD' or error == 'FIRMWARE' or error == 'BED_DISCONNECT':
                #disable features
                self.extruder.button_state = True
                self.manual.button_state = True

                #swap error icon
                self.error_icon = "Icons/Printer Status/failure_icon_red.png"
                self.error_color_adapter = self.white_color

            elif error == 'DEFAULT':
                self.extruder.button_state = False
                self.manual.button_state = False

                self.error_icon = "Icons/check_icon.png"
                
            else:
                self.extruder.button_state = False
                self.manual.button_state = False

                #swap error icon
                self.error_icon = "Icons/failure_icon.png"    
                self.error_color_adapter = self.white_color   
        
        

    def grab_target_and_actual(self, tool):
        acceptable_tools = {'tool0': 'tool0',
                        'tool1': 'tool1',
                        'bed' : 'bed'
        }

        actual = 0
        target = 0

        if tool in acceptable_tools:
            temps = roboprinter.printer_instance._printer.get_current_temperatures()

            if tool in temps:
                if 'actual' in temps[tool] and 'target' in temps[tool]:
                    if temps[tool]['actual'] == None:
                        actual = 0
                        target = 0
                    else:
                        actual = temps[tool]['actual']
                        target = temps[tool]['target'] 
                else:
                    actual = 0
                    target = 0

        return {'actual':actual, 'target':target}

    def detirmine_layout(self):
        printer_type = roboprinter.printer_instance._settings.global_get(['printerProfiles', 'defaultProfile'])
        model = printer_type['model']

        tool0 = False
        tool1 = False
        bed = False


        
        if printer_type['extruder']['count'] == 1:
            tool0 = True
        elif printer_type['extruder']['count'] > 1:
            tool0 = True
            tool1 = True
        if printer_type['heatedBed']:
            bed = True
        

        if tool0 and tool1 and bed:
            tool_0 = Tool_Status(roboprinter.lang.pack['Tool_Status']['Tool1'], "tool0")
            tool_1 = Tool_Status(roboprinter.lang.pack['Tool_Status']['Tool2'], "tool1")
            bed = Tool_Status(roboprinter.lang.pack['Tool_Status']['Bed'], "bed")

            self.ids.tools.add_widget(tool_0)
            self.ids.tools.add_widget(tool_1)
            self.ids.tools.add_widget(bed)

        elif tool0 and bed:
            tool_0 = Tool_Status(roboprinter.lang.pack['Tool_Status']['Tool'], "tool0")
            bed = Tool_Status(roboprinter.lang.pack['Tool_Status']['Bed'], "bed")
            self.ids.tools.add_widget(tool_0)
            self.ids.tools.add_widget(Label())
            self.ids.tools.add_widget(bed)
            
            
        elif tool0:
            tool_0 = Tool_Status(roboprinter.lang.pack['Tool_Status']['Tool'], "tool0")
            self.ids.tools.add_widget(Label())
            self.ids.tools.add_widget(tool_0)
            self.ids.tools.add_widget(Label())
            
            
            
            
        else:
            Logger.info("##################### TOOL STATUS ERROR #######################")

    def turn_off_splash(self, dt):
        temp1 = self.grab_target_and_actual('tool0')
        self.extruder_one_max_temp = temp1['target']
        self.extruder_one_temp = temp1['actual']

        temp2 = self.grab_target_and_actual('tool1')
        self.extruder_two_max_temp = temp2['target']
        self.extruder_two_temp = temp2['actual']

        bed = self.grab_target_and_actual('bed')
        self.bed_max_temp = bed['target']
        self.bed_temp = bed['actual']
        #turn off the splash screen
        if self.extruder_one_temp != 0 and self.startup == False:
            #Logger.info("Turning Off the Splash Screen!")
            self.detirmine_layout()
            #check for updates
            self.check_updates()
            #check for updates every hour
            Clock.schedule_interval(self.update_clock, 3600)
            self.startup = True
             
            
            return False

    def update_clock(self, dt):
        current_data = roboprinter.printer_instance._printer.get_current_data()
        is_printing = current_data['state']['flags']['printing']
        is_paused = current_data['state']['flags']['paused']

        if not is_printing and not is_paused:
            self.check_updates()

    def check_updates(self):
        self.updates = UpdateScreen(populate=False)
        self.updates.refresh_versions()
        installed = self.updates.get_installed_version()
        available = self.updates.get_avail_version()

        Logger.info("Available: " + available.encode('utf-8') + " Installed: " + installed.encode('utf-8') )

        if installed < available and available != roboprinter.lang.pack['Update_Printer']['Connection_Error'] and not self.update_lock:
            self.update_lock = True
            #updater popup
            update = Update_Warning_Popup(self.run_update, self.unlock_updater)
            update.open()

    def run_update(self):
        self.updates.run_updater()

    def unlock_updater(self):
        self.update_lock = False



    def safety(self,dt):
        self.safety_counter += 1
        safety_time = 60

        if self.safety_counter == safety_time and self.startup == False:
            self.detirmine_layout()
            self.check_updates()
            Clock.unschedule(self.splash_event)
            return False
        elif self.safety_counter == safety_time and self.startup == True:
            return False

class Idle_Screen(BoxLayout):
    def __init__(self):
        super(Idle_Screen, self). __init__()
        pass

    

class Print_Screen(BoxLayout):

    filename = StringProperty("")
    status = StringProperty("None")
    bed_max_temp = NumericProperty(200)
    bed_temp = NumericProperty(0)
    progress = StringProperty('')
    progress_number = NumericProperty(50)
    startup = False 
    safety_counter = 0
    update_lock = False
    etr = StringProperty("Error")
    te = StringProperty("Error")
    etr_start_time = -999
    te_start_time = -999
    first_round = True
    progress_width = NumericProperty(200)

    
    

    def __init__(self):
        super(Print_Screen, self).__init__()
        Clock.schedule_interval(self.update, 0.2)
        self.te_start_time = time.time()

        #initialize the screen
        self.update(0)
        

    def parse_time(self, time):
        m, s = divmod(time, 60)
        h, m = divmod(m, 60)

        time_dict = {'hours': int(h),
                     'minutes': int(m),
                     'seconds': int(s)
                     }

        return time_dict


    def update(self, dt):
        
        # temps = roboprinter.printer_instance._printer.get_current_temperatures()
        current_data = roboprinter.printer_instance._printer.get_current_data()
        filename = current_data['job']['file']['name']
        is_operational = current_data['state']['flags']['operational']
        is_ready = current_data['state']['flags']['ready']
        is_printing = current_data['state']['flags']['printing']
        is_paused = current_data['state']['flags']['paused']
        progress = current_data['progress']['completion']
        self.status = current_data['state']['text']
        print_time_left = current_data['progress']['printTimeLeft']
        current_time = current_data['progress']['printTime']
        

        
        self.filename = filename.replace('.gcode','') if filename else ''

        
        self.progress_width = self.ids.progress_bar_goes_here.width
        if progress != None:
            self.progress_number = (float(progress) / 100.00) * float(self.progress_width)
            p_transformed = int(progress)
            self.progress = '[size=40]{}'.format(p_transformed) + roboprinter.lang.pack['Printer_Status']['Percent'] + '[/size]'

        if current_time != None:
            time_elapsed = self.parse_time(current_time)
            self.te = "{0:02d}:".format(time_elapsed['hours']) + "{0:02d}".format(time_elapsed['minutes']) 
        else:
            self.te = ''

        if print_time_left != None:
            time_remaining = self.parse_time(print_time_left)
            if int(time_remaining['hours']) == 0 and int(time_remaining['minutes']) == 0:
                self.etr = roboprinter.lang.pack['Printer_Status']['Minute_Left']
            else:
                self.etr = "{0:02d}:".format(time_remaining['hours']) + "{0:02d}".format(time_remaining['minutes']) 
        else:
            self.etr = ''
        


        if progress == 100:
            roboprinter.printer_instance._printer.unselect_file()  
            return False

        if progress == None:
            return False     

class StartPauseButton(Auto_Image_Label_Button):
    def __init__(self, **kwargs):
        #text, image_icon, background_normal, callback
        self.button_text = '[size=30]' + roboprinter.lang.pack['File_Screen']['Pause'] + '[/size]'
        self.image_icon = "Icons/Printer Status/pause_button_icon.png"
        self.background_normal = "Icons/blue_button_style.png"
        self.callback = self.toggle_pause_print

        super(StartPauseButton, self).__init__(self.button_text, self.image_icon, self.background_normal, self.callback)
        Clock.schedule_interval(self.sync_with_devices, .1)
        Clock.schedule_interval(self.colors, .1)
        self.auto_pause_pop = None

    def toggle_pause_print(self):
        roboprinter.printer_instance._printer.toggle_pause_print()


    def sync_with_devices(self, dt):
        '''makes sure that button's state syncs up with the commands that other devices push to the printer '''
        is_paused = roboprinter.printer_instance._printer.is_paused()
        if is_paused and self.button_text ==  '[size=30]{}[/size]'.format(roboprinter.lang.pack['File_Screen']['Pause']):
            self.button_text =  '[size=30]{}[/size]'.format(roboprinter.lang.pack['File_Screen']['Resume'])
            self.image_icon = 'Icons/Manual_Control/start_button_icon.png'
        elif not is_paused and self.button_text ==  '[size=30]{}[/size]'.format(roboprinter.lang.pack['File_Screen']['Resume']):
            self.button_text =  '[size=30]{}[/size]'.format(roboprinter.lang.pack['File_Screen']['Pause'])
            self.image_icon = "Icons/Printer Status/pause_button_icon.png"
            self.auto_pause_pop = None

    def colors(self, dt):
        '''updates the color  of the button based on Start or Pause state. Green for Start'''
        is_paused = roboprinter.printer_instance._printer.is_paused()
        if is_paused:
            self.background_normal = 'Icons/green_button_style.png'

        else:
            self.background_normal = 'Icons/blue_button_style.png'

class CancelButton(Auto_Image_Label_Button):

    def __init__(self):
        #button_text, image_icon, background_normal, callback
        self.button_text = '[size=30]' + roboprinter.lang.pack['File_Screen']['Cancel'] + '[/size]'
        self.image_icon = "Icons/Printer Status/cancel_button_icon.png"
        self.background_normal = "Icons/red_button_style.png"
        self.callback = self.modal_view
        super(CancelButton, self).__init__(self.button_text, self.image_icon, self.background_normal, self.callback)

    def cancel_print(self, *args):
        Clock.schedule_once(self.cancel_callback, 0.5)

    def cancel_callback(self, dt):
        if self.is_printing() or roboprinter.printer_instance._printer.is_paused() == True:
            roboprinter.printer_instance._printer.cancel_print()
            Logger.info('Cancellation: Successful')
            self.mv.dismiss()

    def modal_view(self):
        self.mv = ModalPopup(self.cancel_print)
        self.mv.open()

    def is_printing(self):
        """ whether the printer is currently operational and ready for a new print job"""
        printing = roboprinter.printer_instance._printer.is_printing()
        if not printing:
            return False
        else:
            return True

class Motor_Control_Button(Button):
    """docstring for Motor_Control_Button"""
    button_state = ObjectProperty(False)
    lang = roboprinter.lang
    def __init__(self):
        super(Motor_Control_Button, self).__init__()
        pass

class Temp_Control_Button(Button):
    """docstring for Motor_Control_Button"""
    button_state = ObjectProperty(False)
    lang = roboprinter.lang
    def __init__(self):
        super(Temp_Control_Button, self).__init__()
        pass
        

class ModalPopup(ModalView):

    def __init__(self, yes_callback):
        super(ModalPopup, self).__init__()
        self.yes_callback = yes_callback
        self.populate_buttons()
        
    def cancellation_feedback(self):
        self.ids.modal_question.text = roboprinter.lang.pack['File_Screen']['Canceling']

    def cancel_popup(self, *args):
        self.cancellation_feedback()
        self.yes_callback()
    def dismiss_pop(self, **kwargs):
        self.dismiss()


    def populate_buttons(self):
        content = self.ids.yes_no_grid

        yes_button = Auto_Image_Label_Button('[size=30]' + roboprinter.lang.pack['Popup']['PYes'], 'Icons/Manual_Control/ok_button_icon.png', 'Icons/blue_button_style.png', self.cancel_popup)
        no_button = Auto_Image_Label_Button('[size=30]' + roboprinter.lang.pack['Popup']['PNo'], 'Icons/Manual_Control/cancel_button_icon.png', 'Icons/red_button_style.png', self.dismiss_pop)
        

        content.add_widget(yes_button)
        content.add_widget(no_button)

class Tool_Status(BoxLayout):
    name = StringProperty("Error")
    current_temperature = NumericProperty(0.0)
    max_temp = NumericProperty(0.0)
    tool = StringProperty('tool0')
    progress = NumericProperty(0)

    def __init__(self, name, tool, **kwargs):
        super(Tool_Status, self).__init__(**kwargs)
        self.name = name
        self.tool = tool
        Clock.schedule_interval(self.update_temp_and_progress, .1)

    def update_temp_and_progress(self, dt):
        self.temperature()


    def temperature(self):
        temps  = roboprinter.printer_instance._printer.get_current_temperatures()
        
        try:
            self.current_temperature = temps[self.tool]['actual']
            
            self.max_temp = temps[self.tool]['target']

            #round to one decimal place so that the numbers can fit on the screen 
            if isinstance(self.current_temperature, float):
                self.current_temperature = round(self.current_temperature,1)
            else:
                self.current_temperature = float(self.current_temperature)

            if isinstance(self.max_temp, float):
                self.max_temp = round(self.max_temp, 1)
            else:
                self.max_temp = float(self.max_temp)



            if self.tool == 'bed':
                if 'bed' in pconsole.temperature:
                    if float(pconsole.temperature['bed']) <= 0:
                        self.current_temperature = 0.0

        except Exception as e:
            #Logger.info("Temperature Error")
            if self.tool == 'bed':
                if 'bed' in pconsole.temperature:
                    if float(pconsole.temperature['bed']) <= 0:
                        self.current_temperature = 0.0
          
        
class Custom_Progress_Bar(FloatLayout):
    """docstring for Custom_Progress_Bar"""
    progress_width = NumericProperty(350)
    progress_height = NumericProperty(50)
    progress = NumericProperty(0)


    def __init__(self, progress_width, progress_height, progress):
        super(Custom_Progress_Bar, self).__init__()
        self.progress_width = progress_width
        self.progress_height = progress_height
        self.progress = progress
            
