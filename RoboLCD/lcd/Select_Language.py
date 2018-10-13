# -*- coding: utf-8 -*-
# @Author: Matt Pedler
# @Date:   2017-07-14 17:04:43
# @Last Modified by:   Matt Pedler
# @Last Modified time: 2017-10-27 13:13:49
from common_screens import Modal_Question, Button_Screen, Title_Button_Screen
from scrollbox import Scroll_Box_Even, Scroll_Box_Even_Button
from functools import partial
from .. import roboprinter
from Language import lang
import subprocess
from kivy.clock import Clock
from kivy.logger import Logger

class Change_Language():

    def __init__(self):
        self.select_language()

    def select_language(self):
        layout = Select_Language(self.confirmation)

        title = lang.pack['Switch_Lang']['Welcome']['Title']
        name = 'select_language'
        back_destination = 'options'

        roboprinter.back_screen(
            name=name,
            title=title,
            back_destination=back_destination,
            content=layout
        )

    def confirmation(self, action, language=None,lang_option = None, **kwargs):

        if action and language != None:
            self.old_language = lang.current_lang
            lang.reload_language(lang_option)
            roboprinter.printer_instance._settings.set(['Language'], lang_option)
            roboprinter.printer_instance._settings.save()
            
            layout = Language_Confirmation_Screen(language)
    
            title = lang.pack['Switch_Lang']['Confirmation']['Title'] + language
            name = 'confirm_language'
            back_destination = roboprinter.robo_screen()
    
            roboprinter.back_screen(
                name=name,
                title=title,
                back_destination=back_destination,
                content=layout
            )
            Clock.schedule_interval(self.Monitor_Screen, 0.2)

        else:
            self.select_language()

    def Monitor_Screen(self, dt):

        if roboprinter.robosm.current != 'confirm_language':
            lang.reload_language(self.old_language)
            roboprinter.printer_instance._settings.set(['Language'], self.old_language)
            roboprinter.printer_instance._settings.save()
            Logger.info("Switched Back to old language LC: " + str(self.old_language))
            return False


    

#screens
class Select_Language(Scroll_Box_Even):
    def __init__(self, callback):

        self.acceptable_languages = {'English': 'en',
                                     'Spanish': 'sp',
                                     'Giberish': 'gib'
                               }
        self.callback = callback
        self.load_buttons()

        super(Select_Language, self).__init__(self.buttons)

    def load_buttons(self):
        self.buttons = []
        for option in self.acceptable_languages:
            temp_button = Scroll_Box_Even_Button(option, self.populate, {option : self.acceptable_languages[option]})
            self.buttons.append(temp_button)

    def populate(self, language=None, **kwargs):
        #there should be only one entry in the dictionary
        for option in language:
            layout = Switch_Language(option, self.callback, language[option])
            title = lang.pack['Switch_Lang']['Choose']['Select'] + option + lang.pack['Switch_Lang']['Choose']['Question']
            name = 'yes_no_language'
            back_destination = roboprinter.robo_screen()
    
            roboprinter.back_screen(
                name=name,
                title=title,
                back_destination=back_destination,
                content=layout
            )


class Switch_Language(Modal_Question):
    #self, title, body_text, option1_text, option2_text, option1_function, option2_function
    def __init__(self, language, callback, lang_option):
        #temporarily switch to new language
        self.old_language = lang.current_lang
        self.switch_language(lang_option)

        self.title = lang.pack['Switch_Lang']['Choose']['Switch_to'] + language + lang.pack['Switch_Lang']['Choose']['Question']
        self.body_text = lang.pack['Switch_Lang']['Choose']['Are_You_Sure']
        self.option1_text = lang.pack['Switch_Lang']['Choose']['Yes_option']
        self.option2_text = lang.pack['Switch_Lang']['Choose']['No_option']
        self.option1_function = self.yes
        self.option2_function = self.no 

        self.callback = callback
        self.language = language
        self.lang_option = lang_option
        self.pressed_yes = False
        


        super(Switch_Language, self).__init__(self.title, self.body_text, self.option1_text, self.option2_text, self.option1_function, self.option2_function)
        Clock.schedule_interval(self.Monitor_Screen, 0.2)

    def yes(self):
        self.pressed_yes = True
        self.callback(True, language=self.language, lang_option = self.lang_option)

    def no(self):
        self.switch_language(self.old_language)
        self.callback(False)    

    def switch_language(self, lang_option):
        lang.reload_language(lang_option)

    def Monitor_Screen(self, dt):

        if roboprinter.robosm.current != 'select_language' and not self.pressed_yes:
            lang.reload_language(self.old_language)
            Logger.info("Switched Back to old language LC: " + str(self.old_language))
            return False

class Language_Confirmation_Screen(Button_Screen):
    #self, body_text, button_function, button_text = roboprinter.lang.pack['Button_Screen']['Default_Button'], **kwargs

    def __init__(self, language):
        self.body_text = lang.pack['Switch_Lang']['Confirmation']['Body1'] + language + lang.pack['Switch_Lang']['Confirmation']['Body2']

        self.button_function = self.restart
        self.button_text = lang.pack['Switch_Lang']['Confirmation']['Button']


        super(Language_Confirmation_Screen, self).__init__(self.body_text, self.button_function, button_text=self.button_text)

    def restart(self):
        subprocess.call('/home/pi/scripts/webcam stop & sudo pkill -9 octoprint & sudo service octoprint restart', shell=True)




