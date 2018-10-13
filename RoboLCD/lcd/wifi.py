# -*- coding: utf-8 -*-
# @Author: Matt Pedler
# @Date:   2017-09-18 15:07:34
# @Last Modified by:   Matt Pedler
# @Last Modified time: 2017-12-06 15:19:07
from RoboLCD import roboprinter
from kivy.uix.screenmanager import Screen
from kivy.properties import ObjectProperty, StringProperty, BooleanProperty, NumericProperty
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.core.window import Window
from kivy.uix.vkeyboard import VKeyboard
from kivy.logger import Logger
from kivy.uix.image import Image
from kivy.graphics import *
from kivy.uix.widget import Widget
from kivy.clock import Clock
from kivy.uix.gridlayout import GridLayout
import thread
from functools import partial
from kivy.core.window import Window
from scrollbox import Scroll_Box_Even

from netconnectd import NetconnectdClient
import base64

class QR_Button(Button):
    pass

class IPAddressButton(Button):
    pass

class WifiConfigureButton(Button):
    pass

class APButton(Button):
    pass

class AP_Mode():
    counter = 0
    ap_mode_start = False
    ap_mode_fail = False
    def __init__(self, robosm, name, **kwargs):
        self.sm = robosm
        self.name = name #name of initial screen
        self.title = roboprinter.lang.pack['WiFi']['AP_Title']
        self.ap_mode_1_4()
        self.settings = roboprinter.printer_instance._settings


    def ap_mode_1_4(self, **kwargs):
        c = AP_Mode_1_4(self)
        Logger.info('starting ap mode')
        self.sm._generate_backbutton_screen(name=self.name, title=self.title, back_destination='network_utilities_screen', content=c)

    def ap_mode_2_4(self, **kwargs):
        c = Screen(name=self.name + '[2]')
        s = AP_Mode_2_4(self)
        c.add_widget(s)

        self.sm.add_widget(c)
        self.sm.current = c.name

        #start the hotspot
        self.generate_ap_confirmation_screen()

        Clock.schedule_interval(self.ap_mode_2_4_callback, .5)

    def ap_mode_2_4_callback(self, dt):
        if self.ap_mode_start == True:
            self.ap_mode_success()
            Logger.info('Started AP Mode Successfully')
            return False
        elif self.ap_mode_fail == True:
            self.ap_mode_failure()
            Logger.info('Failed to start AP Mode')
            return False


    def ap_mode_failure(self, **kwargs):
        c = Screen(name=self.name+'[3]')
        s = AP_Mode_Failure(self)
        c.add_widget(s)

        self.sm.add_widget(c)
        self.sm.current = c.name


    def ap_mode_success(self, **kwargs):
        c = Screen(name=self.name+'[4]')
        s = AP_Mode_Success(self)
        c.add_widget(s)


        self.sm.add_widget(c)
        self.sm.current = c.name

        self.save_connection_info()

    def generate_ap_confirmation_screen(self, **kwargs):
        self.ap_mode_fail = False
        self.ap_mode_start = False

        def connect():
            ap_mode_start = False
            try:
                netcon = NetconnectdClient()
                netcon.command('forget_wifi', None)
                netcon.command('start_ap', None)
                self.ap_mode_start = True
            except Exception as e:
                self.ap_mode_fail = True
                Logger.error('Start AP: {}'.format(e))


        thread.start_new_thread(connect, ())
        return

    def retry(self):
        #reset the AP Mode
        netcon = NetconnectdClient()
        netcon.command('reset', None)
        #retry
        self.ap_mode_2_4()

    def save_connection_info(self):
        self.settings.set(['tester'], 'sure')
        self.settings.save()




class AP_Mode_1_4(FloatLayout):
    def __init__(self, ap_mode):
        super(AP_Mode_1_4, self).__init__()
        Logger.info('ap 1/4')
        self.ap = ap_mode


class AP_Mode_2_4(FloatLayout):
    def __init__(self, ap_mode):
        super(AP_Mode_2_4, self).__init__()
        self.ap = ap_mode

class AP_Mode_Failure(BoxLayout):
    def __init__(self, ap_mode):
        super(AP_Mode_Failure, self).__init__()
        self.ap = ap_mode

class AP_Mode_Success(FloatLayout):
    def __init__(self, ap_mode):
        super(AP_Mode_Success, self).__init__()
        self.ap = ap_mode

class APConfirmation(Label):
    text = StringProperty(roboprinter.lang.pack['WiFi']['Initiating'])

class StartAPButton(Button):
    pass


class APConfirmation(Label):
    text = StringProperty(roboprinter.lang.pack['WiFi']['Initiating'])


class WifiButton(Button):
    ssid = StringProperty('')
    encrypted = BooleanProperty(False)
    quality = NumericProperty(0)

    def __init__(self, *args, **kwargs):
        super(WifiButton, self).__init__(*args, **kwargs)
        #self.text = self.ssid
        self.format()

    def format(self):
        pass

        #if the ssid is empty name it so
        if self.ssid == '':
            self.ssid = roboprinter.lang.pack['WiFi']['Empty_SSID']

        #switch out locked or unlocked ssid
        if self.encrypted != True:
            self.ids.wifi_encrypted.source = 'Icons/rounded_black.png'

        #change flip the signal strength from negative to positive.
        signal_quality = int(self.quality )
        signal_quality *= -1


        #switch out different PNGs
        if signal_quality >= 81:
            Logger.info('wifi 1 ' + str(signal_quality))
            self.ids.wifi_signal.source = 'Icons/wifi_1.png'
        elif signal_quality >= 68 and signal_quality <= 80:
            Logger.info('wifi 2 ' + str(signal_quality))
            self.ids.wifi_signal.source = 'Icons/wifi_2.png'
        elif signal_quality >= 31 and signal_quality <= 67:
            Logger.info('wifi 3 ' + str(signal_quality))
            self.ids.wifi_signal.source = 'Icons/wifi_3.png'
        elif signal_quality >= 0 and signal_quality <= 30:
            Logger.info('wifi 4 ' + str(signal_quality))
            self.ids.wifi_signal.source = 'Icons/wifi_4.png'


class WifiPasswordInput(FloatLayout, object):
    """
    Manages the wifi password input layout and its child widgets. Main functionality -- display password and keyboard, allow user to input password with keyboard, allow user to toggle between different keyboards (letters, special characters, and numbers)
    """
    ssid = StringProperty('')
    kbContainer = ObjectProperty()
    _password_buffer = ''

    def __init__(self, **kwargs):
        super(WifiPasswordInput, self).__init__(**kwargs)
        self.ssid = kwargs['ssid']
        self._keyboard = None
        self._set_keyboard('keyboards/abc.json')
        self.settings = roboprinter.printer_instance._settings

        saved_pword = self.check_for_password()
        if  saved_pword != False:

            self.password_buffer = saved_pword
            self.ids.password.text = '*' * len(self.password_buffer)

    @property
    def password_buffer(self):
        return self._password_buffer

    @password_buffer.setter
    def password_buffer(self, update):
        self._password_buffer = update

    def check_for_password(self):
        saved_wifi = self.settings.get(['Wifi'])

        if self.ssid in saved_wifi:
            pw = self.cypher_decrypt(self.ssid, saved_wifi[self.ssid])
            return pw
        else:
            return False

    def cypher_decrypt(self,key, string):
        decoded_chars = []
        string = base64.urlsafe_b64decode(string)
        for i in xrange(len(string)):
            key_c = key[i % len(key)]
            encoded_c = chr(abs(ord(string[i]) - ord(key_c) % 256))
            decoded_chars.append(encoded_c)
        decoded_string = "".join(decoded_chars)
        return decoded_string
        
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
        if self.ids.password.text == roboprinter.lang.pack['WiFi']['Enter_Password']: #clear stub text with first keyboard push
            self.ids.password.text = ''
            self.password_buffer = ''
        if keycode == 'backspace':
            self.ids.password.text = self.ids.password.text[:-1]
            self.password_buffer = self.password_buffer[:-1]
        elif keycode == 'capslock' or keycode == 'normal' or keycode == 'special':
            pass
        elif keycode == 'toggle':
            self.toggle_keyboard()
        else:
            self.ids.password.text = '*' * len(self.ids.password.text)
            self.ids.password.text += text
            self.password_buffer += text

    def toggle_keyboard(self):
        # Logger.info('Current Keyboard: {}'.format(dir(self._keyboard)))
        if self._keyboard.layout == "keyboards/abc.json":
            # self.ids.toggle_keyboard.text = "abcABC"
            self._keyboard.layout = "keyboards/123.json"
        else:
            # self.ids.toggle_keyboard.text = "123#+="
            self._keyboard.layout = "keyboards/abc.json"

class WifiUnencrypted(FloatLayout):
    """
    for cases where wifi is not encrypted
    """
    ssid = StringProperty('')
    def __init__(self, **kwargs):
        super(WifiUnencrypted, self).__init__()
        self.ssid = kwargs['ssid']

class WifiConfirmation(FloatLayout):
    ssid = StringProperty('')

class WifiFailure(BoxLayout):
    callback = ObjectProperty(None)
    def __init__(self, callback, **kwargs):
        self.callback = callback
        super(WifiFailure, self).__init__()

class SuccessButton(Button):
    current_screen = StringProperty('') #Deprecated 8/24 No longer necessary since this button is binded to go_back_to_main which only takes self as argument

class WifiConnecting(FloatLayout):
    ssid = StringProperty('')

class WifiLoadingList(FloatLayout):
    pass

class WifiConfiguration(Widget):
    """
    Handles the wifi configuration flow
        wifi list => connect => connecting... => feedback
    """
    wifi_status = 'nothing'
    counter = 0
    def __init__(self, roboscreenmanager, back_destination, *args, **kwargs):
        # generate init screen: aka wifi list screen
        super(WifiConfiguration, self).__init__()
        self.rsm = roboscreenmanager
        self.name = 'wifi_config'
        self.back_destination = back_destination
        self.generate_wifi_list_screen()
        self.settings = roboprinter.printer_instance._settings
        

    def save_connection_info(self):
        #self.wifi_data = {'ssid': ssid, 'psk': psk, 'force': True}
        saved_wifi = self.settings.get(['Wifi'])

        pw = self.cypher_encrypt(self.wifi_data['ssid'], self.wifi_data['psk'])

        if self.wifi_data['ssid'] not in saved_wifi:
            
            saved_wifi[self.wifi_data['ssid']] = pw
            self.settings.set(['Wifi'], saved_wifi, force=True)
            self.settings.save(force=True)

        elif saved_wifi[self.wifi_data['ssid']] != pw:

            saved_wifi[self.wifi_data['ssid']] = pw
            self.settings.set(['Wifi'], saved_wifi, force=True)
            self.settings.save(force=True)

    def cypher_encrypt(self,key, string):
        encoded_chars = []
        for i in xrange(len(string)):
            key_c = key[i % len(key)]
            encoded_c = chr(ord(string[i]) + ord(key_c) % 256)
            encoded_chars.append(encoded_c)
        encoded_string = "".join(encoded_chars)
        return base64.urlsafe_b64encode(encoded_string)

    def generate_wifi_list_screen(self):
        self.wifi_grid = GridLayout(cols=1, padding=0, spacing=0)
        self.placeholder = WifiLoadingList()

        self.wifi_grid.add_widget(self.placeholder)



        self.rsm._generate_backbutton_screen(
            name=self.name,
            title=roboprinter.lang.pack['WiFi']['Select_Network'],
            back_destination=self.back_destination,
            content=self.wifi_grid,
            cta=self._refresh_wifi_list,
            icon='Icons/Manual_Control/refresh_icon.png')

        thread.start_new_thread(self._append_wifi_list, ())
        Clock.schedule_interval(self._wifi_callback, 1 / 30.)
        return

    def generate_configuration_screen(self, ssid, encrypted, *args, **kwargs):
        if encrypted:
            c = WifiPasswordInput(ssid=ssid, id='encrypted')
        else:
            c = WifiUnencrypted(ssid=ssid)
        connect = partial(self.generate_connecting_screen, c)
        c.ids.connect.bind(on_press=connect)
        self.rsm._generate_backbutton_screen(
            name=self.name+'[1]',
            title=ssid,
            back_destination=self.name,
            content=c
        )

        return

    def generate_connecting_screen(self, obj, *args):
        # remove keyboard from screen
        self.wifi_status = 'nothing'
        Window.release_all_keyboards()

        # wifi credentials
        if obj.id == 'encrypted':
            psk = obj.password_buffer
        else:
            psk = ''
        ssid = obj.ssid
        self.wifi_data = {'ssid': ssid, 'psk': psk, 'force': True}

        # layout for connecting screen
        s = Screen(name=self.name+'[2]')
        c = WifiConnecting(ssid=ssid)
        s.add_widget(c)
        self.rsm.add_widget(s)
        self.rsm.current = s.name
        self.temp_screen = s

        thread.start_new_thread(self.connectWifi_thread, ())
        Clock.schedule_interval(self.connectWifi_callback, 1)
        #self.generate_confirmation_screen(s)
    def connectWifi_callback(self, dt):
        self.counter += 1

        if self.wifi_status != 'nothing':
            if self.wifi_status == 'success':
                self.counter = 0
                Logger.info('Connected to WIFI Succesfully')
                ssid = self.wifi_data['ssid']
                self._generate_success_screen(ssid)
                self.rsm.remove_widget(self.temp_screen)
                self.save_connection_info()
                return False
            else:
                self.counter = 0
                Logger.info('Connected to WIFI Unsuccesfully')
                ssid = self.wifi_data['ssid']
                self._generate_failure_screen(ssid)
                self.rsm.remove_widget(self.temp_screen)
                return False
        elif self.counter > 120:
            self.counter = 0
            Logger.info('Connected to WIFI Unsuccesfully')
            ssid = self.wifi_data['ssid']
            self._generate_failure_screen(ssid)
            return False


    def connectWifi_thread(self):
        self.wifi_status = self._connect(self.wifi_data)
        Logger.info(self.wifi_status)

        return


    def _generate_success_screen(self, ssid, *args):
        name = self.name+'success'
        if name in self.rsm.screens:
            self.rms.current = name
        else:
            s = Screen(name=name)
            c = WifiConfirmation(ssid=ssid)
            s.add_widget(c)

            self.rsm.add_widget(s)
            self.rsm.current = s.name

    def _generate_failure_screen(self, *args):
        name  = self.name+'failure'
        if name in self.rsm.screens:
            self.rms.current = name
        else:
            s = Screen(name=name)
            c = WifiFailure(self._retry_config)
            s.add_widget(c)

            self.rsm.add_widget(s)
            self.rsm.current = s.name

    def _retry_config(self, *args):
        self.rsm.go_back_to_screen(self.rsm.current, self.name+'[1]')

    def _connect(self, data):
        try:
            NetconnectdClient().command('configure_wifi', data)
            return 'success'
        except Exception as e:
            return

    def _append_wifi_list(self):
        self.wifi_list = []
        self.wifi_list = NetconnectdClient().command('list_wifi', None)

    def _refresh_wifi_list(self, *args):
        self.wifi_grid.clear_widgets()
        self.wifi_grid.add_widget(self.placeholder)
        thread.start_new_thread(self._append_wifi_list, ())
        Clock.schedule_interval(self._wifi_callback, 1 / 30.)

    def _wifi_callback(self, *args):
        if self.wifi_list != []:
            self.wifi_grid.clear_widgets()
            buttons = []
            for w in self.wifi_list:
                ssid = w['ssid']
                encrypted = w['encrypted']
                quality = w['quality']
                b = WifiButton(ssid=ssid, encrypted=encrypted, quality=quality)
                config_screen = partial(self.generate_configuration_screen, b.ssid, b.encrypted)
                b.bind(on_press=config_screen)
                buttons.append([b, w['quality']])

                buttons.sort(key = lambda quality: quality[1], reverse = True)

                sorted_buttons = []

                for button in buttons:
                    sorted_buttons.append(button[0])

            layout = Scroll_Box_Even(sorted_buttons)
            self.wifi_grid.add_widget(layout)
            Logger.info('Wifi_Callback Is now Uncheduling itself')
            return False
