from RoboLCD.lcd.scrollbox import Scroll_Box_Even 
from RoboLCD.lcd.update_system.Update_Interface import Update_Interface
from RoboLCD import roboprinter
from RoboLCD.lcd.common_screens import Modal_Question_No_Title
from RoboLCD.lcd.connection_popup import Error_Popup, Warning_Popup

#kivy
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import ObjectProperty, StringProperty, BooleanProperty, NumericProperty
from kivy.logger import Logger
from kivy.clock import Clock

#python
import json


class Update_System(Scroll_Box_Even):
    """docstring for Update_System"""
    def __init__(self):
        self.update_interface = Update_Interface()
        self.buttons = self.make_buttons()        
        super(Update_System, self).__init__(self.buttons)
        if self.buttons == []:
            ep = Error_Popup(roboprinter.lang.pack['Update_Printer']['Server_Error']['Title'], roboprinter.lang.pack['Update_Printer']['Server_Error']['Body'])
            ep.show()

    def make_buttons(self):
        updates = self.update_interface.get_updates()

        if updates:
            update_buttons = []
            installed_ver = None
            for update in updates:
                if 'installed' in update:
                    if not update['installed']:
                        update_buttons.append(Install_Button(update))
                    else:
                        installed_ver = []
                        installed_ver.append(Install_Button(update))

            if installed_ver == None:
                return update_buttons
            else:
                return installed_ver + update_buttons
        else:
            return []

class Install_Button(BoxLayout):
    disabled = ObjectProperty(False)
    button_text = StringProperty("")
    install_text = StringProperty("Install")


    def __init__(self, button_data):
        self.update_interface = Update_Interface()
        self.button_data = button_data

        if 'name' in self.button_data and 'version' in self.button_data:
            self.button_text = str(self.button_data['name'] + ": " + self.button_data['version'])

        if 'installed' in self.button_data:
            self.disabled = self.button_data['installed']
            if self.disabled:
                self.install_text = "Installed"
            else:
                self.install_text = "Install"

        super(Install_Button, self).__init__()

    def button_function(self):
        #get the current screen to go back to 
        back_destination = roboprinter.robosm.current

        #this function starts the update
        def goto_update(dt):
            Logger.info("Selecting Update: "  + str(json.dumps(self.button_data, indent=4)))
            if not self.update_interface.select_update(self.button_data):
                #if the update does not go through then throw an error and tell the user
                self.warning.dismiss()
                ep = Error_Popup(roboprinter.lang.pack['Update_Printer']['Server_Error']['Title'], roboprinter.lang.pack['Update_Printer']['Server_Error']['Body'], cancel)
                ep.show()

        #this function displays a loading screen so the user knows that the update is loading and nothing is frozen
        def loading_popup():
            self.warning = Warning_Popup(roboprinter.lang.pack['Update_Printer']['Loading']['Title'], roboprinter.lang.pack['Update_Printer']['Loading']['Body'])
            self.warning.show()

            Clock.schedule_once(goto_update, 0.2)

        #this goes back to the last screen
        def cancel(*args, **kwargs):
            roboprinter.robosm.current = back_destination

        #this created the modal screen for confirming that you want to update
        def update_warning():
            body_text = roboprinter.lang.pack['Update_Printer']['Update_Warning']['Body']
            option1 = roboprinter.lang.pack['Update_Printer']['Update_Warning']['Option1']
            option2 = roboprinter.lang.pack['Update_Printer']['Update_Warning']['Option2']
            modal_screen = Modal_Question_No_Title(body_text, 
                                                   option1, 
                                                   option2, 
                                                   loading_popup, 
                                                   cancel
                                                   )
            name = 'update'
            title = roboprinter.lang.pack['Update_Printer']['Update_Warning']['Title']
            
            roboprinter.back_screen(name=name,
                                    title=title,
                                    back_destination=back_destination,
                                    content=modal_screen
                                )
        #this executes everything
        update_warning()
        






        
        