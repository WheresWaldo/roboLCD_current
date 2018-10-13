# -*- coding: utf-8 -*-
# @Author: Matt Pedler
# @Date:   2017-07-14 12:42:48
# @Last Modified by:   Matt Pedler
# @Last Modified time: 2017-10-27 13:12:16
import subprocess
from kivy.logger import Logger
from common_screens import Title_Button_Screen
from .. import roboprinter
from kivy.clock import Clock
from Language import lang

class webcam():
    def __init__(self):
        pass
    #get state of the webcam
    def get_cam(self):
        webcam = False
        try:
            pid = subprocess.check_output(['pgrep', "mjpg_streamer"] )
            if pid:
                webcam = True
        except Exception as e:
            # Logger.info("Error Occured in Webcam Class")
            pass
        return webcam
    def start(self):
        subprocess.call(['/home/pi/scripts/webcam start'], shell=True)
    def stop(self):
        subprocess.call(['/home/pi/scripts/webcam stop'], shell=True)

class Camera(Title_Button_Screen):
    #title_text, body_text, button_function, button_text = "OK", **kwargs
    def __init__(self):
        self.webcam = webcam()
        self.title_text = lang.pack['Webcam']['Sub_Title']
        self.body_text = lang.pack['Webcam']['Body']
        self.button_text = lang.pack['Webcam']['Button']
        self.check_state()
        Clock.schedule_interval(self.check_status, 0.2)        
        super(Camera, self).__init__(self.title_text, self.body_text, self.button_function, button_text=self.button_text)

    def check_state(self):
        self.cam_on = self.webcam.get_cam()
        self.title_text = lang.pack['Webcam']['Webcam_On'] if self.cam_on else lang.pack['Webcam']['Webcam_Off']
        self.body_text = lang.pack['Webcam']['Body']
        self.button_text = lang.pack['Webcam']['Button_Off'] if self.cam_on else lang.pack['Webcam']['Button_On']
        self.button_function = self.webcam.stop if self.cam_on else self.webcam.start


    def check_status(self, dt):
        self.check_state()

        #exit the clock if we arent on the screen anymore
        if roboprinter.robosm.current != 'webcam_status':
            return False




