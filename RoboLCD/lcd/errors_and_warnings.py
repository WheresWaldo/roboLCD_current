# -*- coding: utf-8 -*-
# @Author: Matt Pedler
# @Date:   2017-09-28 12:22:30
# @Last Modified by:   Matt Pedler
# @Last Modified time: 2018-01-10 09:18:47
# coding=utf-8
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import ObjectProperty, StringProperty, BooleanProperty, NumericProperty, ListProperty
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.logger import Logger
from kivy.clock import Clock
from RoboLCD import roboprinter
import math
import subprocess
from pconsole import pconsole
from session_saver import session_saver
import time
from RoboLCD.lcd.common_screens import Modal_Question_No_Title, Button_Screen, Picture_Button_Screen, Title_Button_Screen
from RoboLCD.lcd.wizards.bed_calibration.bed_calibration_wizard import Modal_Question
from common_screens import Button_Screen, Picture_Button_Screen, Title_Button_Screen
from RoboLCD.lcd.wizards.wizard_overseer import Wizards

from functools import partial
from kivy.core.window import Window

#Re-Enable when RRUs server is deployed
#from RoboLCD.lcd.update_system.Update_Interface import Update_Interface

class Refresh_Screen(Title_Button_Screen):
    # title_text, body_text, image_source, button_function, button_text = "OK", **kwargs
    bed_checker = None
    def __init__(self, title_text, body_text, button_text, bed_disconnect=False, start_refresh=False, **kwargs):
        self.clock_monitor = None
        self.changed_text = False
        self.reconnect_choice = button_text
        self.bed_disconnect = bed_disconnect
        self.start_refresh = start_refresh

        if self.bed_disconnect:
            if self.bed_checker != None:
                self.bed_checker.cancel()
                self.bed_checker = None

        Clock.schedule_interval(self.check_for_screen_change, 0.2)
        session_saver.register_event_updater("Refresh_screen", self.on_event)

        super(Refresh_Screen, self).__init__(title_text, body_text, self.reset, button_text)

        #Immediately start the refresh function as if someone had pressed the button
        if self.start_refresh:
            self.reset()

    def on_event(self, event, payload):
        Logger.info("Event!")
        Logger.info(str(event))
        Logger.info(str(payload))

        if event == "PrinterStateChanged":
            if 'state_id' in payload:
                state = payload['state_id']
                if state == 'CONNECTING':
                    if self.clock_monitor == None:
                        self.clock_monitor = Clock.schedule_interval(self.update_connection_status, 0.2)
                    



    def soft_reset(self):
        current_data = roboprinter.printer_instance._printer.get_current_data()
        status = current_data['state']['text']
        if status.find("Offline") != -1:
            status = roboprinter.lang.pack['Refresh_Screen']['Soft_Reset']['Status']

        reset_title = roboprinter.lang.pack['Refresh_Screen']['Soft_Reset']['Title']
        body_text = (roboprinter.lang.pack['Refresh_Screen']['Soft_Reset']['Please'] + str(self.reconnect_choice).lower()
                     + roboprinter.lang.pack['Refresh_Screen']['Soft_Reset']['Body'] 
                     + '[color=FF0000]'  + status.replace("Error:","").strip() + '[/color]'
                     )
        self.title_text = reset_title
        self.body_text = body_text
        

    def reset(self):
        self.changed_text = False
        self.title = str(self.reconnect_choice) + roboprinter.lang.pack['Refresh_Screen']['Reset']['Title']
        self.body_text = roboprinter.lang.pack['Refresh_Screen']['Reset']['Body']

        def reconnect(dt):
            roboprinter.printer_instance._printer.disconnect()
            if self.clock_monitor == None:
                self.clock_monitor = Clock.schedule_interval(self.update_connection_status, 0.2)
            else:
                self.clock_monitor.cancel()
                self.clock_monitor = Clock.schedule_interval(self.update_connection_status, 0.2)
            Clock.schedule_once(self.connect, 2)    
        Clock.schedule_once(reconnect, 0.5)    

    def connect(self, dt):
        roboprinter.printer_instance._printer.connect()

    def slow_operational(self, dt):
        current_data = roboprinter.printer_instance._printer.get_current_data()
        status = current_data['state']['text']

        self.title_text = str(self.reconnect_choice) + roboprinter.lang.pack['Refresh_Screen']['Update_Connection']['Successful']
        self.body_text = status
        if self.clock_monitor != None:
            self.clock_monitor.cancel()
        Clock.schedule_interval(self.check_connection_reset, 0.2)
        Clock.schedule_once(self.return_to_main, 2)

    def return_to_main(self, dt):
        roboprinter.robosm.go_back_to_main('printer_status_tab')

    def slow_disconnect(self, dt):
        current_data = roboprinter.printer_instance._printer.get_current_data()
        status = current_data['state']['text']

        self.title_text = str(self.reconnect_choice) + roboprinter.lang.pack['Refresh_Screen']['Update_Connection']['In_Progress']

        if status.find("Offline") != -1:
            self.body_text = "Offline"

    def error_report(self, status):

        self.title_text = roboprinter.lang.pack['Refresh_Screen']['Soft_Reset']['Title']
        self.body_text = (roboprinter.lang.pack['Refresh_Screen']['Soft_Reset']['Please'] + str(self.reconnect_choice).lower()
                     + roboprinter.lang.pack['Refresh_Screen']['Soft_Reset']['Body'] 
                     + '[color=FF0000]'  + status.replace("Error:","").strip() + '[/color]'
                     )
        if self.clock_monitor != None:
            self.clock_monitor.cancel()
        Clock.schedule_interval(self.check_connection_reset, 0.2)
        
    def update_connection_status(self, dt):
        current_data = roboprinter.printer_instance._printer.get_current_data()
        status = current_data['state']['text']

        if status == 'Operational':
            #if it's operational say so
            if not self.bed_disconnect:
                Clock.schedule_once(self.slow_operational, 0.5)
            #if we are looking for a bed disconnect say so
            else:
                self.title_text = roboprinter.lang.pack['Refresh_Screen']['Update_Connection']['bed_connect']
                if self.bed_checker != None:
                    self.bed_checker.cancel()
                    self.bed_checker = Clock.schedule_interval(self.check_for_bed, 0.2)
                else:
                    self.bed_checker = Clock.schedule_interval(self.check_for_bed, 0.2)
            return False
        elif self.error_checker(status):
            return False
        else:
            if not self.changed_text:
                Clock.schedule_once(self.slow_disconnect, 0.5)
                self.changed_text = True

        if status.find("Offline") != -1:
            self.body_text = roboprinter.lang.pack['Refresh_Screen']['Update_Connection']['offline']
        else:
            self.body_text = status

        current_screen = str(roboprinter.robosm.current) 

        if current_screen != 'mainboard' and current_screen != 'mainboard_status':
            return False

    def check_for_bed(self, dt):
        if float(pconsole.temperature['bed']) > 0.00:
            Clock.schedule_once(self.slow_operational, 0.5)
            return False

        current_screen = str(roboprinter.robosm.current) 
        if current_screen != 'mainboard' and current_screen != 'mainboard_status':
            return False

    def check_connection_reset(self, dt):
        current_data = roboprinter.printer_instance._printer.get_current_data()
        status = current_data['state']['text']

        if status.find("Offline") != -1:
            self.soft_reset()
            return False

        current_screen = str(roboprinter.robosm.current) 

        if current_screen != 'mainboard' and current_screen != 'mainboard_status':
            return False

    #TODO Expand to cover all potential errors
    def error_checker(self, status):
        if status.find("Error") != -1:
            # Logger.info(str(status))
            # # pull the actual error out of the string
            # # example error: "Error: Connection error, see Terminal tab"
            # e1 = status.find(":") + 1
            # e2 = status.find(",")
            # if e1 == -1:
            #     e1 = 0
            # if e2 == -1:
            #     e2 = len(status)
            # actual_error = status[e1:e2].strip()
            self.error_report(str(status))
            return True
        else:
            return False

    def check_for_screen_change(self, dt):

        current_screen = str(roboprinter.robosm.current) 


        if current_screen != 'mainboard' and current_screen != 'mainboard_status':
            session_saver.unregister_event_updater("Refresh_screen")
            return False



class Firmware_Upgrade(Picture_Button_Screen):
    #title_text, body_text, image_source, button_function
    """docstring for Firmware_Upgrade"""
    def __init__(self):
        self.title = roboprinter.lang.pack['Firmware']['Title']
        self.body = roboprinter.lang.pack['Firmware']['Body']
        self.icon = "Icons/Printer Status/Firmware warning.png"
        super(Firmware_Upgrade, self).__init__(self.title, self.body, self.icon, self.goto_main)

    def goto_main(self):
        roboprinter.robosm.go_back_to_main('printer_status_tab')
    
class Bed_Heating(Picture_Button_Screen):
    #title_text, body_text, image_source, button_function
    """docstring for Bed_Heating"""
    def __init__(self):
        self.title = roboprinter.lang.pack['Bed_Hot']['Title']
        self.body = roboprinter.lang.pack['Bed_Hot']['Body']
        self.icon = "Icons/Printer Status/bed heating.png"
        super(Bed_Heating, self).__init__(self.title, self.body, self.icon, self.goto_main)
    def goto_main(self):
        roboprinter.robosm.go_back_to_main('printer_status_tab')

class Filament_Runout(Modal_Question):
    #title, body_text, option1_text, option2_text, option1_function, option2_function
    def __init__(self):
        self.title = roboprinter.lang.pack['Filament']['Title']
        self.body_text = roboprinter.lang.pack['Filament']['Body']
        wiz = Wizards(soft_load=True, back_destination='main')
        func = partial(wiz.load_wizard, generator='FIL_LOAD')
        super(Filament_Runout, self).__init__(self.title, self.body_text,roboprinter.lang.pack['Filament']['Button1'], roboprinter.lang.pack['Filament']['Button2'], self.goto_main, func)

    def goto_main(self):
        roboprinter.robosm.go_back_to_main('printer_status_tab')

class Error_Detection(Button):
    """docstring for Error_Detection"""
    #warning / error system
    bed_max_temp = NumericProperty(200)
    bed_temp = NumericProperty(0)
    error_title = StringProperty("")
    error_body = StringProperty("")
    error_icon = StringProperty("Icons/Printer Status/blank-warning.png")
    error_function = ObjectProperty(None)
    last_error = "NONE"
    pause_lock = False
    caret_size = NumericProperty(0.0)
    firm_lock = False
    update_message = StringProperty("")
    update_available = False

    first_default = False

    def __init__(self):
        super(Error_Detection, self).__init__()
        Clock.schedule_interval(self.check_connection_status, 0.2)

        #set a timer to check for updates
        #self.check_update_available(1)
        #Clock.schedule_interval(self.check_update_available, 3600)
        
    def populate_error(self, error):

        acceptable_errors = {
            'MAINBOARD': {
                'title': roboprinter.lang.pack['Error_Detection']['MAINBOARD']['Title'],
                'body' : roboprinter.lang.pack['Error_Detection']['MAINBOARD']['Body'],
                'icon' : "Icons/Printer Status/main board warning.png",
                'function': self.main_board_disconnect,
                'caret': True
            },
            'FIRMWARE':{
                'title': roboprinter.lang.pack['Error_Detection']['FIRMWARE']['Title'],
                'body' :roboprinter.lang.pack['Error_Detection']['FIRMWARE']['Body'],
                'icon' : "Icons/Printer Status/Firmware warning.png",
                'function': self.firmware_updating,
                'caret': True,
            },
            'BED_HOT':{
                'title': roboprinter.lang.pack['Error_Detection']['BED_HOT']['Title'],
                'body' : roboprinter.lang.pack['Error_Detection']['BED_HOT']['Body'],
                'icon' : "Icons/Printer Status/bed heating.png",
                'function': self.bed_hot_warning,
                'caret': True,
            },
            'BED_DISCONNECT':{
                'title': roboprinter.lang.pack['Error_Detection']['BED_DISCONNECT']['Title'],
                'body' : roboprinter.lang.pack['Error_Detection']['BED_DISCONNECT']['Body'],
                'icon' : "Icons/Printer Status/bed warning.png",
                'function': self.bed_disconnect_screen,
                'caret': True,
            },
            'PAUSED':{
                'title': roboprinter.lang.pack['Error_Detection']['PAUSED']['Title'],
                'body' : "[color=#69B3E7]" + roboprinter.lang.pack['Error_Detection']['PAUSED']['Body'],
                'icon' : "Icons/Printer Status/Pause.png",
                'function': self.placeholder,
                'caret': False
            },
            'FIL_RUNOUT':{
                'title': roboprinter.lang.pack['Error_Detection']['FIL_RUNOUT']['Title'],
                'body' : roboprinter.lang.pack['Error_Detection']['FIL_RUNOUT']['Body'],
                'icon' : "Icons/Printer Status/Filament warning.png",
                'function': self.fil_runout,
                'caret': True
            },
            'UPDATE_AVAILABLE': {
                'title': roboprinter.lang.pack['Error_Detection']['UPDATE_AVAILABLE']['Title'],
                'body' : "[color=#69B3E7]" + self.update_message + roboprinter.lang.pack['Error_Detection']['UPDATE_AVAILABLE']['Body'],
                'icon' : 'Icons/White_Utilities/Updates.png',
                'function': self.update_warning,
                'caret': True
            },
            'NONE':{
                'title': "",
                'body' : "",
                'icon' : "Icons/Printer Status/blank-warning.png",
                'function': self.placeholder,
                'caret': False
            },
            'DEFAULT':{
                'title': roboprinter.lang.pack['Error_Detection']['DEFAULT']['Title_Idle'] if not roboprinter.printer_instance._printer.is_printing() else roboprinter.lang.pack['Error_Detection']['DEFAULT']['Title_Active'],
                'body' : "[color=#69B3E7]" + roboprinter.lang.pack['Error_Detection']['DEFAULT']['Body_Idle'] + "[/color]" if not roboprinter.printer_instance._printer.is_printing() else "[color=#69B3E7]" + roboprinter.lang.pack['Error_Detection']['DEFAULT']['Body_Active'] + "[/color]",
                'icon' : "Icons/check_icon.png",
                'function': self.placeholder,
                'caret': False
            }

        }

        if error in acceptable_errors:
            session_saver.saved['current_error'] = error
            self.error_title = acceptable_errors[error]['title']
            self.error_body = acceptable_errors[error]['body']
            self.error_icon = acceptable_errors[error]['icon']
            self.error_function = acceptable_errors[error]['function']

            if acceptable_errors[error]['caret']:
                self.caret_size = 0.2
            else:
                self.caret_size = 0.0

            #if the error is not a warning, then pop the error
            if error is not 'BED_HOT' and error is not 'DEFAULT' and error is not self.last_error:
                acceptable_errors[error]['function']()

                #kill any attached keyboard
                Window.release_all_keyboards()
        else:
            session_saver.saved['current_error'] = 'DEFAULT'
            self.error_title = acceptable_errors['DEFAULT']['title']
            self.error_body = acceptable_errors['DEFAULT']['body']
            self.error_icon = acceptable_errors['DEFAULT']['icon']
            self.error_function = acceptable_errors['DEFAULT']['function']

        #check to see if this is the first error to populate the system. If it is then kill the splash screen
        if not self.first_default:
            self.first_default = True
            subprocess.call(['sudo pkill omxplayer'], shell=True)

        self.last_error = error

    #this is used so we don't get error on press
    def placeholder(self):
        pass

    def bed_disconnect_screen(self):
       
        title = '[color=FF0000]' + roboprinter.lang.pack['Error_Detection']['BED_DISCONNECT']['E_Sub_Title'] + '[/color]'
        body_text = roboprinter.lang.pack['Error_Detection']['BED_DISCONNECT']['E_Body']
        button_text = roboprinter.lang.pack['Error_Detection']['BED_DISCONNECT']['E_Button']
            
        layout = Refresh_Screen(title, body_text, button_text, bed_disconnect=True)

        title = roboprinter.lang.pack['Error_Detection']['BED_DISCONNECT']['E_Title']
        name = 'mainboard'
        back_destination = 'main'

        roboprinter.back_screen(
            name=name,
            title=title,
            back_destination=back_destination,
            content=layout
        )

    def bed_hot_warning(self):
        layout = Bed_Heating()

        title = roboprinter.lang.pack['Error_Detection']['BED_DISCONNECT']['E_Title']
        name = 'bed_warning'
        back_destination = 'main'

        roboprinter.back_screen(
            name=name,
            title=title,
            back_destination=back_destination,
            content=layout
        )

    def firmware_updating(self):
        layout = Firmware_Upgrade()

        title = roboprinter.lang.pack['Error_Detection']['FIRMWARE']['E_Title']
        name = 'firmware_update'
        back_destination = 'main'

        roboprinter.back_screen(
            name=name,
            title=title,
            back_destination=back_destination,
            content=layout
        )

    def main_board_disconnect(self):
        current_screen = roboprinter.robosm.current

        if current_screen != 'mainboard' and current_screen != 'mainboard_status':

            current_data = roboprinter.printer_instance._printer.get_current_data()
            status = current_data['state']['text']
            if status.find("Offline") != -1:
                status = roboprinter.lang.pack['Error_Detection']['MAINBOARD']['Connection_Offline']
            elif status.find("Printing") != -1:
                while status == "Printing":
                    current_data = roboprinter.printer_instance._printer.get_current_data()
                    status = current_data['state']['text']

            reset_title = roboprinter.lang.pack['Error_Detection']['MAINBOARD']['E_Sub_Title']
            body_text = (roboprinter.lang.pack['Error_Detection']['MAINBOARD']['E_Body'] + '[color=FF0000]'  + status.replace("Error:","").strip() + '[/color]'
                     )
            button_text = roboprinter.lang.pack['Error_Detection']['MAINBOARD']['E_Button']
            
            layout = Refresh_Screen(reset_title, body_text, button_text)
    
            title =roboprinter.lang.pack['Error_Detection']['MAINBOARD']['E_Title']
            name = 'mainboard'
            back_destination = 'main'
    
            roboprinter.back_screen(
                name=name,
                title=title,
                back_destination=back_destination,
                content=layout
            )
    def fil_runout(self):
        layout = Filament_Runout()

        title = roboprinter.lang.pack['Error_Detection']['FIL_RUNOUT']['E_Title']
        name = 'fil_runout'
        back_destination = 'main'

        roboprinter.back_screen(
            name=name,
            title=title,
            back_destination=back_destination,
            content=layout
        )

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

    def check_update_available(self, dt):
        ui = Update_Interface()
        updates = ui.get_updates()
        if updates != False:
            for update in updates:
                if 'installed' in update and not update['installed']:
                    if 'name' in update and 'version' in update:
                        self.update_message = str(update['name'] + ": " + update['version'])
                    else:
                        self.update_message = ""
                    Logger.info("Update Available")
                    self.update_available = True
                    return True
        

    def update_warning(self):

        def goto_update():
            roboprinter.robosm.generate_screens('UPDATES')

        def cancel():
            roboprinter.robosm.go_back_to_main('printer_status_tab')


        def update_warning():
            title = roboprinter.lang.pack['Error_Detection']['UPDATE_AVAILABLE']['E_Title']
            body_text = roboprinter.lang.pack['Error_Detection']['UPDATE_AVAILABLE']['E_Body']
            option1 = roboprinter.lang.pack['Error_Detection']['UPDATE_AVAILABLE']['E_Update']
            option2 = roboprinter.lang.pack['Error_Detection']['UPDATE_AVAILABLE']['E_Cancel']
            modal_screen = Modal_Question(title,
                                          body_text, 
                                          option1, 
                                          option2, 
                                          goto_update, 
                                          cancel
                                          )
            name = 'update_warning'
            title = roboprinter.lang.pack['Error_Detection']['UPDATE_AVAILABLE']['Second_Title']
            back_destination = roboprinter.robosm.current
            roboprinter.back_screen(name=name,
                                    title=title,
                                    back_destination=back_destination,
                                    content=modal_screen
                                )
        update_warning()

    
        


    ############################################Detirmine Errors##################################################

    def check_connection_status(self, dt):
        self.model = roboprinter.printer_instance._settings.get(['Model'])
        bed = self.grab_target_and_actual('bed')
        self.bed_max_temp = bed['target']
        self.bed_temp = bed['actual']
        is_closed_or_error = roboprinter.printer_instance._printer.is_closed_or_error()
        is_updating_firm = roboprinter.printer_instance.firmware_updating()
        is_printing = roboprinter.printer_instance._printer.is_printing()
        is_paused = roboprinter.printer_instance._printer.is_paused()
        auto_pause = False

        #get the filament status
        if roboprinter.printer_instance.check_auto_pause != None:
            auto_pause = roboprinter.printer_instance.check_auto_pause()
            if auto_pause:
                Logger.info("Auto Pause Equals True!")

                   

        #unlock the pause on restart of the print
        if is_printing and self.pause_lock:
            self.pause_lock = False
        elif not is_printing and not is_paused and self.pause_lock:
            self.pause_lock = False

        if roboprinter.printer_instance._printer.get_current_connection()[0] == 'Closed':
            is_closed = True
        else:
            is_closed = False

        is_error = roboprinter.printer_instance._printer.is_error()

        #Lock the firmware update in and wait for it to be done
        if is_updating_firm and not self.firm_lock:
            self.firm_lock = True
            Logger.info("Firm Lock Active")
        elif not is_updating_firm and is_closed and self.firm_lock:
            #connect to the printer
            Logger.info("Re connecting the printer")
            roboprinter.printer_instance._printer.connect()
        elif not is_updating_firm and not is_closed and self.firm_lock:
            self.firm_lock = False
            current_screen = roboprinter.robosm.current
            if current_screen == 'firmware_update':
                roboprinter.robosm.go_back_to_main('printer_status_tab')

        if is_closed and not is_updating_firm and not self.firm_lock:
            if 'bed' in pconsole.temperature and self.model == "Robo R2":
                if float(pconsole.temperature['bed']) < 0:
                    #self.connection_popup = self.generate_connection_popup(warning = 'bed')
                    self.populate_error('BED_DISCONNECT')
                else:
                    #self.connection_popup = self.generate_connection_popup(warning = 'main')
                    self.populate_error('MAINBOARD')
            else:
                self.populate_error('MAINBOARD')

        elif is_error and not is_updating_firm and not self.firm_lock :
            if 'bed' in pconsole.temperature and self.model == "Robo R2":
                if float(pconsole.temperature['bed']) < 0:
                    #self.connection_popup = self.generate_connection_popup(warning = 'bed')
                    self.populate_error('BED_DISCONNECT')
                else:
                    #self.connection_popup = self.generate_connection_popup(warning = 'main')
                    self.populate_error('MAINBOARD')
            else:
                #self.connection_popup = self.generate_connection_popup(warning = 'main')
                self.populate_error('MAINBOARD')

        elif is_paused and not auto_pause and not self.pause_lock:
            self.populate_error('PAUSED')
        elif auto_pause or self.pause_lock:
            if not self.pause_lock:
                Logger.info("Auto Paused")
                self.pause_lock = True
                self.populate_error("FIL_RUNOUT")
            else:
                if self.pause_lock:
                    pass #don't populate any error
        elif self.bed_max_temp > 0 and not is_error and not is_closed and not is_updating_firm and not self.pause_lock:
            self.populate_error('BED_HOT')

        elif is_updating_firm:
            self.populate_error('FIRMWARE')
        elif self.update_available:
            self.populate_error('UPDATE_AVAILABLE')
        else:
            self.populate_error('DEFAULT')

        

    ############################################Detirmine Errors##################################################
            
        


        
        
