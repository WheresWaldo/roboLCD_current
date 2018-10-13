# -*- coding: utf-8 -*-
# @Author: Matt Pedler
# @Date:   2017-09-18 15:07:34
# @Last Modified by:   Matt Pedler
# @Last Modified time: 2017-10-27 13:13:39
class Session_Saver():
    """docstring for Session_Saver"""
    event_updaters = {}
    def __init__(self):
        self.saved = {'saved': 'I am a saver'}

    def save_variable(self, name, value):
        self.saved[name] = value

    def register_event_updater(self, name, function):
        #Logger.info("Registered Function" + str(function))
        self.event_updaters[name] = function

    def unregister_event_updater(self, name):
        if name in self.event_updaters:
            del self.event_updaters[name]
        
    def update_event(self, event, payload):

        
        for updater in self.event_updaters:
            self.event_updaters[updater](event, payload)


session_saver = Session_Saver()