# -*- coding: utf-8 -*-
# @Author: Matt Pedler
# @Date:   2017-10-16 15:04:49
# @Last Modified by:   Matt Pedler
# @Last Modified time: 2018-01-28 15:58:54

#Kivy
from kivy.uix.screenmanager import Screen
from kivy.properties import ObjectProperty, StringProperty
from kivy.logger import Logger

#RoboLCD
from RoboLCD import roboprinter
from RoboLCD.lcd.file_system.file_back_button import File_BB

#python
import copy
from functools import partial


class Wizard_BB(File_BB):

    def __init__(self):
        super(Wizard_BB, self).__init__()
        self.group_dictionary = {}
        self.screen = None
        self.name="Wizard_BB"
        self.back_destination = roboprinter.robosm.current
        self.delete_same_name_screens()

    def delete_same_name_screens(self):
        for s in roboprinter.robosm.screen_names:
            if s is self.name:
                d = roboprinter.robosm.get_screen(s)
                roboprinter.robosm.remove_widget(d)
                Logger.info("Removed Duplicate Screen: " + s)
                for s in roboprinter.robosm.screen_names:
                    Logger.info(str(s))
        
    

    
    
    def make_screen(self, content, title, back_function='original', option_function='original', option_icon="Icons/settings.png", **kwargs):
        ###############################################################################
        #                         Screen Flow Controls                                #
        ###############################################################################
    
        '''
        Make screen is used to make new screens inside of the back button class. It keeps track of each screen and puts it into
        a linked list so we can keep track of screens that came before and repopulate them as the need arises. 
        '''

        
        if back_function == 'original':
            bf = self.back_function_flow
        else:
            bf = back_function

        self.set_screen_content(content, title, back_function=bf, option_function=option_function, option_icon=option_icon)
        
        #grab current screen
        current_screen = self.get_screen_data()

        #Main screen linked list
        self.screen = Screen_Node(screen=current_screen, prev_screen=self.screen)

        #check to see that we are the current screen if we are not then make us the current screen
        if roboprinter.robosm.current != self.name:
            roboprinter.robosm.current = self.name


    def back_function_flow(self,**kwargs):


        #check to see if the screen has an update function
        if hasattr(self.content, 'change_screen_event') and callable(self.content.change_screen_event):
            self.content.change_screen_event()

        
        if hasattr(self, 'screen') and self.screen.return_previous() != None:
            #go back to previous link
            self.screen = self.screen.return_previous()

            Logger.info("Moving back to screen: " + str(self.screen.screen['title']))

            #clear widgets
    
            #populate old screen
            old_screen = self.screen.screen
            self.populate_old_screen(old_screen)
        else:
            Logger.info("Went back as far as possible")

            Logger.info("Attempting to go back to chosen back destination")
            try:
                #go back to chosen place
                roboprinter.robosm.current = self.back_destination
                Logger.info("Successfully went back")
            except Exception as e:
                Logger.info("Screen did not exist, Exiting to main")
                roboprinter.robosm.current = 'main'
            

    def show_current_screen(self):
        old_screen = self.screen.screen
        self.populate_old_screen(old_screen)

    def go_back_to_screen_with_title(self, title, **kwargs):
        
        
        copy_node = self.screen

        while copy_node != None:
            if copy_node.screen['title'] == title:
                break
            else:
                copy_node = copy_node.return_previous()

        #populate screen
        if copy_node != None:
            while self.screen != None:
                if self.screen.screen['title'] == title:
                    break
                else:
                    self.screen = self.screen.return_previous()
            self.group_dictionary = {} #reset group dictionary to nothing
            self.show_current_screen()
        else:
            Logger.info("No screen with title: " + str(title))
            return False

    def does_screen_exist(self, title):
        copy_node = self.screen

        while copy_node != None:
            if copy_node.screen['title'] == title:
                return True
            else:
                copy_node = copy_node.return_previous()
        return False # return false if we do not find the screen

    def delete_node(self):
        #clean the Nodes
        while self.screen.prev_screen != None:
            del_list = []
            for content in self.screen.screen:
                del_list.append(content)
            #delete the content
            for content in del_list:
                self.screen.screen[content] = ''
                del self.screen.screen[content]

            #iterate to next node
            self.screen = self.screen.return_previous_with_cleanup()
        #delete nodes
        del self.screen.prev_screen
        del self.screen.screen
        del self.screen

'''
Screen node holds a linked list of screens to go backward to
'''
class Screen_Node(object):
    screen=None
    prev_screen = None
    def __init__(self, screen=None, prev_screen=None, **kwargs):
        self.screen = screen
        self.prev_screen = prev_screen

    def return_previous(self):
        return self.prev_screen

    def return_previous_with_cleanup(self):
        if (self.screen!= None and 
            'content' in self.screen and 
            hasattr(self.screen['content'], "cleanup") and 
            callable(self.screen['content'].cleanup)):
            self.screen['content'].cleanup()
        return self.prev_screen


