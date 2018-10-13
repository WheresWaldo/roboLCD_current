# -*- coding: utf-8 -*-
# @Author: Matt Pedler
# @Date:   2017-10-27 13:07:21
# @Last Modified by:   Matt Pedler
# @Last Modified time: 2018-01-28 14:51:55

#kivy
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.logger import Logger
from kivy.properties import ObjectProperty, StringProperty, BooleanProperty, NumericProperty, ListProperty
from kivy.clock import Clock

#RoboLCD
from RoboLCD import roboprinter
from RoboLCD.lcd.printer_jog import printer_jog
from RoboLCD.lcd.pconsole import pconsole
from RoboLCD.lcd.scrollbox import Scroll_Box_Even, Scroll_Box_Even_Button
from RoboLCD.lcd.common_screens import Button_Screen, Temperature_Wait_Screen, Modal_Question, Picture_Button_Screen, Extruder_Selector
from RoboLCD.lcd.wizards.FTZO.circle_plotter import circle_plotter
from RoboLCD.lcd.wizards.FTZO.console_watcher import Console_Watcher

#python
import math
import gc
import weakref

#lines mod
class Update_Offset(BoxLayout, object):
    i_toggle_mm = ListProperty(['Icons/Manual_Control/increments_2_1.png', 'Icons/Manual_Control/increments_2_2.png'])
    s_toggle_mm = ListProperty(['0.01mm', '0.05mm'])
    f_toggle_mm = ListProperty([0.01, 0.05])
    toggle_mm = NumericProperty(0)
    actual_offset = NumericProperty(0)
    line_lock = BooleanProperty(False)
    _mode = None
    _x_pos = 0
    last_pos = [0,0,0,0,0,0]
    cw = None

    #this variable is used by parent class
    title = roboprinter.lang.pack['FT_ZOffset_Wizard']['Welcome']['Title']

    
    def __init__(self, mode, back_button):
        super(Update_Offset, self).__init__()
        self.bb = back_button
        self.offset = 0.00
        #get the mode and set the mode
        self.mode = mode
        self.line_lock = False

        #get the current offset
        self.actual_offset = str(pconsole.home_offset['Z'])


    def cleanup(self):
        Logger.info("######## Cleaner for Update_Offset")
        for item in self.__dict__:
            self.__dict__[item] = None
        
    def update_mode(self, value):
        self.mode = value

    #These getters and setters will act as the interface to set the mode for this class.
    @property
    def mode(self):
        return self._mode

    @mode.setter
    def mode(self, value):
        Logger.info("Updating Mode!")
        self._mode = value
        self.corner = self._mode['corner']
        self.start_pos_x = self._mode['start_pos_x']
        self.start_pos_y = self._mode['start_pos_y']
        self.travel_amount = self._mode['travel_amount']
        self.max_x_travel = self._mode['max_x_travel']
        self.drop_amount = self._mode['drop_amount']
        self.x_pos = int(self._mode['start_pos_x'])

        #unlock button
        self.unlock()

        #throw the setup to the logger
        import json
        Logger.info(str(json.dumps(self._mode, indent=4)))

    @property
    def x_pos(self):
        return self._x_pos

    @x_pos.setter
    def x_pos(self,value):
        self._x_pos = value
        Logger.info("X was changed to: " + str(self.x_pos))

    def toggle_mm_z(self):
        value =  self.toggle_mm + 1
        if value > 1:
            self.toggle_mm = 0
        else:
            self.toggle_mm += 1
        Logger.info(self.s_toggle_mm[self.toggle_mm])

    def set_offset(self):
        updated_offset = self.actual_offset + self.offset
        #take a big float and reduce it to two numbers, then save the new offset
        roboprinter.printer_instance._printer.commands('M206 Z{0:.2f} '.format(updated_offset))
        self.actual_offset = updated_offset
        self.offset = 0
        self.make_shape()

    def add_offset(self):
        self.actual_offset += self.f_toggle_mm[self.toggle_mm]
        
    def subtract_offset(self):
        self.actual_offset -= self.f_toggle_mm[self.toggle_mm]
        
    def make_shape(self):
        #Lock the button
        self.line_lock = True
        Logger.info("Locked!")
            
        pos = pconsole.get_position()
        while not pos:
            pos = pconsole.get_position()
        
        Logger.info("self.x_pos is at: " + str(self.x_pos) + " position x is at: " + str(pos[0]))
        Logger.info("mode is: " + str(self.corner))
        if self.corner == "L2R":
            if float(pos[0]) < self.max_x_travel:
                self._line()
            else:
                self.warn_and_restart()
        elif self.corner == "R2L":
            if float(pos[0]) > self.max_x_travel:
                self._line()
            else:
                self.warn_and_restart()
        elif self.corner == "CIRCLE":
            if float(pos[0]) > self.max_x_travel:
                self._circle()
            else:
                self.warn_and_restart()
        else:
            raise ValueError("self.corner was not set to CIRCLE, R2L, or L2R Current value is: " + str(self.corner))

    def _line(self):
        #start a console watcher
        Console_Watcher(self.unlock)
        roboprinter.printer_instance._printer.commands('G1 Z0.3') #put nozzle on the bed
        roboprinter.printer_instance._printer.commands('G92 E0.00') #reset the E to zero so we can make a line
        roboprinter.printer_instance._printer.commands('G1 E6.00 F1000') #extrude filament
        roboprinter.printer_instance._printer.commands('G1 Y' + str(self.travel_amount) + ' E15.00 F1000') #make a line ratio is 12mm on bed to 1mm extrude for R2
        roboprinter.printer_instance._printer.commands('G1 Z5 E10.00 F1000') #Retract filament and pull nozzle off bed    
        roboprinter.printer_instance._printer.commands("M114")
        Logger.info("self.x_pos is at: "  + str(self.x_pos))  

        #add or subtract based on mode
        if self.corner == "L2R":
            self.x_pos = self.x_pos + 10
            Logger.info("Adding 10")
        elif self.corner == "R2L":
            self.x_pos = self.x_pos - 10
            Logger.info("Subtracting 10")

        Logger.info("self.x_pos is at: "  + str(self.x_pos))
        #Goto next point
        roboprinter.printer_instance._printer.commands('G1 X'+ str(self.x_pos) + ' Y'+ str(self.start_pos_y) + ' F3000') #go to the next line start position
        roboprinter.printer_instance._printer.commands("M114") #Make the serial console busy until the move command has completed
        roboprinter.printer_instance._printer.commands('M118 ACTION COMPLETE!') #Tell the console watcher that the action is complete


    def _circle(self):
        #start Console Watcher
        Console_Watcher(self.unlock)

        #get circle
        cp = circle_plotter()
        radius = cp.distance_between_points([cp.bed_x, cp.bed_y], [self.x_pos, cp.bed_y])
        Logger.info("Making circle with radius of " + str(radius))
        circle = cp.make_circle_points(radius)
        Logger.info("Circle has " + str(len(circle['script'])) + " Points")

        #print circle
        roboprinter.printer_instance._printer.commands('G1 X' + str(circle['start_point'][0]) + " Y" + str(circle['start_point'][1]) + " F3000")
        roboprinter.printer_instance._printer.commands('G1 Z0.3') #put nozzle on the bed
        roboprinter.printer_instance._printer.commands('G92 E0.00') #reset the E to zero so we can prime the head
        roboprinter.printer_instance._printer.commands('G1 E5.20 F500') #extrude filament
        roboprinter.printer_instance._printer.commands('G92 E0.00') #reset the E to zero so we can make a circle
        #make the circle
        roboprinter.printer_instance._printer.commands(circle['script']) #print coordinate of circle

        #lift head
        roboprinter.printer_instance._printer.commands('G1 Z5 E' + str(circle['end_e'] - 5.00) + ' F3000') #Retract filament and pull nozzle off bed 
        roboprinter.printer_instance._printer.commands('M118 ACTION COMPLETE!') #This command will echo back the text we sent it. Another process will pick this up and call a callback

        #alter self.x_pos
        self.x_pos = self.x_pos - 5

    #This function is a callback tied to console_watcher
    def unlock(self):
        Logger.info("Unlocked!")
        self.line_lock = False    

    def warn_and_restart(self):
        Logger.info("Unlocked!")
        self.line_lock = False    
        pos = pconsole.get_position()
        while not pos:
            pos = pconsole.get_position()

        drop = self.drop_amount - float(pos[2]) 
        Logger.info("Dropping to: " + str(drop))

        #################################################################################################################
                                    #Get off of the endstop so the Z axis works...
        #get bed dimensions
        bed_x = roboprinter.printer_instance._settings.global_get(['printerProfiles','defaultProfile', 'volume','width'])
        bed_y = roboprinter.printer_instance._settings.global_get(['printerProfiles','defaultProfile', 'volume','depth'])

        #calculate final positions
        bed_x = float(bed_x) / 2.0
        bed_y = float(bed_y) / 2.0

        roboprinter.printer_instance._printer.commands('G1 X' + str(bed_x) + ' Y' + str(bed_y) +' F3000')
        #################################################################################################################
        
        roboprinter.printer_instance._printer.commands('G1 Z'+ str(drop) + ' F3000')
        roboprinter.printer_instance._printer.commands('G1 X'+ str(self.start_pos_x) + ' Y'+ str(self.start_pos_y) + ' F3000') # go to first corner
        self.warning_screen = Button_Screen(roboprinter.lang.pack['FT_ZOffset_Wizard']['Warn_Restart']['Body'] , self.restart)
        title = roboprinter.lang.pack['FT_ZOffset_Wizard']['Warn_Restart']['Title']

        self.bb.make_screen(self.warning_screen,
                            title,
                            option_function='no_option')


    def restart(self):
        def reposition(dt):
            roboprinter.printer_instance._printer.commands('G1 X'+ str(self.start_pos_x) + ' Y'+ str(self.start_pos_y) + ' F3000') # go to first corner
            roboprinter.printer_instance._printer.commands('G1 Z5')
            self.x_pos = self.start_pos_x
            #update position
            pconsole.get_position()
            pconsole.get_position()
    
            self.go_back_to_FTZO()

        self.warning_screen.body_text = roboprinter.lang.pack['FT_ZOffset_Wizard']['Warn_Restart']['Repositioning']
        Clock.schedule_once(reposition, 0.2)

    #this function will take us back to the FTZO Edit page
    def go_back_to_FTZO(self):
        self.bb.go_back_to_screen_with_title(roboprinter.lang.pack['FT_ZOffset_Wizard']['Welcome']['Title'])
    


class Picture_Instructions(BoxLayout):
    
    def __init__(self):
        super(Picture_Instructions, self).__init__()
        pass  

    def cleanup(self):
        Logger.info("######## Cleaner for Picture_Instructions")
        for item in self.__dict__:
            self.__dict__[item] = None  

class FTZO_Button(Button):
    """docstring for FTZO_Button"""
    icon_text = StringProperty("")
    icon_source = StringProperty("")
    offset = NumericProperty(5)

    def __init__(self, icon_text='', icon_source='', offset = 5, **kwargs):
        super(FTZO_Button, self).__init__(**kwargs)
        self.icon_text = icon_text
        self.icon_source = icon_source

class FTZO_Options(Scroll_Box_Even):
    """docstring for FTZO_Options"""

    #all inputs are callbacks for us to make buttons with
    def __init__(self, dual, mode, set_mode, selected_tool, save_offset, exit_callback, back_button):
        self.buttons = []
        super(FTZO_Options, self).__init__(self.buttons)
        self.bb = back_button
        self.dual = dual
        self.mode = mode
        self.set_mode = set_mode
        self.selected_tool = selected_tool #this is a get/set function of another class
        self.save_offset = save_offset
        self.exit_callback = exit_callback
        self.buttons = None

        #initialize buttons
        self.make_buttons()

        #populate screen
        self.repopulate_for_new_screen()
        

    def cleanup(self):
        Logger.info("########## Cleaning up FTZO_Options")

        #Cleanup buttons
        for button in self.buttons:
            button.cleanup()

        #dereference these bound methods
        self.set_mode = ''
        self.selected_tool = ''
        self.save_offset = ''
        self.exit_callback = ''
        self.bb = ''

        #get rid of the buttons
        self.clear_widgets()
        #remove self from any widgets
        if self.parent:
            self.parent.remove_widget(self)

        #clear self
        del_list = []
        for self_var in self.__dict__:
            del_list.append(self_var)
            self.__dict__[self_var] = ''
        for self_var in del_list:
            #Logger.info("Deleting " + str(self_var))
            del self.__dict__[self_var]
        # Logger.info("---> Printing referrers of FTZO_workflow")
        # gc.collect()
        # for referer in gc.get_referrers(self):
        #     Logger.info(referer)
        # Logger.info("---> Done printing referrers of FTZO_workflow")
        #delete self
        del self

    def placeholder(self, *args, **kwargs):
        Logger.info("Placeholder hit")
        pass

    def make_buttons(self):
        '''make_buttons will make the appropriate options list for whatever setup FTZO is in currently '''
        if self.buttons != None:
            for button in self.buttons:
                button.cleanup()

        self.buttons = []

        #put finish wizard first so it's always visible
        finish_wizard = Scroll_Box_Even_Button(roboprinter.lang.pack['FT_ZOffset_Wizard']['Options']['Save_and_Exit'], self.finish_wizard, "")
        self.buttons.append(finish_wizard)
        if self.mode['corner'] != "CIRCLE":
            set_mode_button = Scroll_Box_Even_Button(roboprinter.lang.pack['FT_ZOffset_Wizard']['Options']['Change_Corner'], 
                              self.user_set_mode, "")
            change_to_circle = Scroll_Box_Even_Button(roboprinter.lang.pack['FT_ZOffset_Wizard']['Options']['Change_Circles'], 
                              self.change_shape, "CIRCLE")
            self.buttons.append(set_mode_button)
            self.buttons.append(change_to_circle)
        else:
            change_to_lines = Scroll_Box_Even_Button(roboprinter.lang.pack['FT_ZOffset_Wizard']['Options']['Change_Lines'], 
                              self.change_shape, "LINES")
            self.buttons.append(change_to_lines)
            

        
        if self.dual:
            change_extruder = Scroll_Box_Even_Button(roboprinter.lang.pack['FT_ZOffset_Wizard']['Options']['Change_Extruder'], 
                              self.change_extruder, "")
            self.buttons.append(change_extruder)
        clear_bed = Scroll_Box_Even_Button(roboprinter.lang.pack['FT_ZOffset_Wizard']['Options']['Clear_Bed'], 
                        self.clear_bed, [self.clear_bed_restart, self.go_back_to_FTZO] )
        #re_calibrate = Scroll_Box_Even_Button(roboprinter.lang.pack['FT_ZOffset_Wizard']['Options']['Recalibrate'], self.re_calibrate_bed, self.go_back_to_FTZO)
        

        self.buttons.append(clear_bed)
        #self.buttons.append(re_calibrate)
        
    
           

    #This function will drop the bed a certain amount then the user will be prompted to clear the bed.
    def clear_bed(self, callback):
        pos = pconsole.get_position()
        while not pos:
            pos = pconsole.get_position()

        drop = self.mode['drop_amount'] - float(pos[2]) 
        Logger.info("Dropping to: " + str(drop))

        #################################################################################################################
                                    #Get off of the endstop so the Z axis works...
        #get bed dimensions
        bed_x = roboprinter.printer_instance._settings.global_get(['printerProfiles','defaultProfile', 'volume','width'])
        bed_y = roboprinter.printer_instance._settings.global_get(['printerProfiles','defaultProfile', 'volume','depth'])

        #calculate final positions
        bed_x = float(bed_x) / 2.0
        bed_y = float(bed_y) / 2.0

        roboprinter.printer_instance._printer.commands('G1 X' + str(bed_x) + ' Y' + str(bed_y) +' F3000')
        #################################################################################################################
        roboprinter.printer_instance._printer.commands('G1 Z'+ str(drop) + ' F3000')
        from functools import partial
        c = partial(callback[0], callback=callback[1])
        layout = Button_Screen(roboprinter.lang.pack['FT_ZOffset_Wizard']['Warn_Restart']['Body'] , c)
        title = roboprinter.lang.pack['FT_ZOffset_Wizard']['Warn_Restart']['Title']

        self.bb.make_screen(layout,
                                                title,
                                                option_function='no_option')
    def clear_bed_restart(self, callback):
        self.set_mode(self.mode['corner']) #reset the current mode
        callback()

    #This function sets the mode for the Lines testing Pattern
    def user_set_mode(self, *args, **kwargs):
        def left_corner():
            self.set_mode("L2R")
            self.go_back_to_FTZO()
        def right_corner():
            self.set_mode("R2L")
            self.go_back_to_FTZO()

        if self.mode['corner'] == "R2L":
            left_corner()
        else:
            right_corner()

        # layout = Modal_Question(roboprinter.lang.pack['FT_ZOffset_Wizard']['Set_Mode']['Sub_Title'] , 
        #                         roboprinter.lang.pack['FT_ZOffset_Wizard']['Set_Mode']['Body'],
        #                         roboprinter.lang.pack['FT_ZOffset_Wizard']['Set_Mode']['Option1'],
        #                         roboprinter.lang.pack['FT_ZOffset_Wizard']['Set_Mode']['Option2'],
        #                         left_corner,
        #                         right_corner
        #                         )
        # title = roboprinter.lang.pack['FT_ZOffset_Wizard']['Set_Mode']['Title']

        # self.bb.make_screen(layout, 
        #                                         title,
        #                                         option_function='no_option')

    def re_calibrate_bed(self, bed_callback):
        def redo_cal(callback=None):
            roboprinter.printer_instance._printer.commands('G36')
            roboprinter.printer_instance._printer.commands('M114')
            roboprinter.printer_instance._printer.commands('M118 ACTION COMPLETE!')
            self.set_mode(self.mode['corner']) #reset the current mode
            callback()

        self.clear_bed([redo_cal, bed_callback])
        

    #This function will change our shape to lines or concentric circles
    def change_shape(self, shape):
        if shape == "CIRCLE":
            self.set_mode("CIRCLE")
            layout = Button_Screen(roboprinter.lang.pack['FT_ZOffset_Wizard']['Change_Pattern']['Body_Text'], self.go_back_to_FTZO)
            title = roboprinter.lang.pack['FT_ZOffset_Wizard']['Change_Pattern']['Title']
            self.bb.make_screen(layout,
                                                    title,
                                                    option_function='no_option')
        else:
            #if we arent setting the shape to circle we are going back to lines. Ask the user to clear the bed then continue
            self.user_set_mode()
        
    #this function will take us back to the FTZO Edit page
    def go_back_to_FTZO(self):
        self.bb.go_back_to_screen_with_title(roboprinter.lang.pack['FT_ZOffset_Wizard']['Welcome']['Title'])

    def change_extruder(self, *args, **kwargs):

        selected_tool = self.selected_tool()
        if selected_tool == 'tool0':
            selected_tool = 'EXT1'
        elif selected_tool == 'tool1':
            selected_tool = "EXT2"
        else:
            Logger.info("Could not find a selected tool, defaulting to tool0")
            selected_tool = "EXT1" #default

        #Only show options for extruder 1 or 2
        es = Extruder_Selector(self.get_selected_extruder, 
                          make_screen=self.bb.make_screen,
                          only_extruder=True,
                          selected_tool=selected_tool 
                          )
        es.show_screen()  


    def get_selected_extruder(self, selected_tool):
        
        if selected_tool == 'EXT1':
            selected_tool = 'tool0'
        elif selected_tool == 'EXT2':
            selected_tool = 'tool1'
        else:
            Logger.info("Wrong Selected tool " + str(selected_tool))
            selected_tool = 'tool0' #default to this if soemthing goes wrong

        Logger.info(selected_tool)
        self.change_tool(selected_tool)

    def change_tool(self, selected_tool):
        #select the new toolhead, This will also change the temp
        self.selected_tool(value=selected_tool)

        #wait for the temperature to change, then go back to the EZO screen
        layout = Temperature_Wait_Screen(self.go_back_to_FTZO, tool_select=selected_tool)
        title="Heating Selected Extruder"
        self.bb.make_screen(layout, 
                                                title,
                                                option_function='no_option')

    def save_z_offset(self, *args, **kwargs):
        
        layout = Z_offset_saver(self.go_back_to_FTZO,
                               [roboprinter.lang.pack['Save_Offset']['Saving'], roboprinter.lang.pack['Save_Offset']['Saved']], 
                               )

        title = roboprinter.lang.pack['FT_ZOffset_Wizard']['Finish']['Title']

        self.bb.make_screen(layout,
                                                title,
                                                option_function="no_option")

    def finish_wizard(self, *args, **kwargs):
        self.go_back_to_FTZO()
        self.exit_callback()

'''
This class is the options for changing the FTZO. The user can change the corner, change the selected extruder,
save the Z-Offset, and Save and Exit the wizard.

Some future options would be:
To change the printing type:
    Change the print from lines to circles. In the future we would like this to print out concentric circles on the bed

The ultimate goal would be to print out a spiral.
'''
class Z_offset_saver(Picture_Button_Screen):
    """docstring for Z_offset_saver"""
    offset_saver = 0.00 #variable so we do no break the screen randomly
    updated_offset = NumericProperty(0.00)
    icons = ListProperty(["Icons/Icon_Buttons/Options.png" , "Icons/Manual_Control/check_icon.png"])
    title_texts = ListProperty(['',''])

    def __init__(self, callback, title_text = ['', ''], **kwargs):
        #title_text, body_text,image_source, button_function, button_text
        self.title_texts = title_text

        #Throw an error if there is not two entries in the title texts
        if len(self.title_texts) != 2:
            raise ValueError("did not supply the correct array length of correct type values for variable self.title_texts")

        title_text = self.title_texts[0]
        body_text = roboprinter.lang.pack['FT_ZOffset_Wizard']['Save_Offset']['Waiting']
        image_source = self.icons[0]
        button_function = self.okay_button
        self.callback = callback

        #save the Z-Offset
        roboprinter.printer_instance._printer.commands('M500')
        pconsole.register_observer('M206', self.update_offset)
        Logger.info("querying eeprom")
        pconsole.query_eeprom()

        super(Z_offset_saver, self).__init__(title_text, body_text, image_source, button_function)

    def cleanup(self):
        #call extended classes cleanup function
        super(Z_offset_saver, self).cleanup()
        #dereference callback
        self.callback = ''

        #deconstruct self
        del_list = []
        for self_var in self.__dict__:
            del_list.append(self_var)
            self.__dict__[self_var] = ''
        for self_var in del_list:
            Logger.info("Deleting " + str(self_var))
            del self.__dict__[self_var]

        #delete self
        del self



    def okay_button(self):
        pconsole.unregister_observer('M206', self.update_offset)
        self.callback()

    #Callback for the wizard bb to hook into when it changes screens
    def change_screen_event(self):
        Logger.info("Changing screens")
        pconsole.unregister_observer('M206', self.update_offset)

    def update_offset(self, value):
        Logger.info("Offset Updating!")
        if 'Z' in value:
            self.offset_saver = value['Z']
            

            #This is an artificial waiting period, but it also kicks processing 
            #back to the kivy thread so that the on screen elements change correctly
            Clock.schedule_once(self.update_success, 0.5)

    def update_success(self, *args, **kwargs):
        #update screen as well
        Logger.info("Updating screen!")
        self.updated_offset = self.offset_saver
        self.image_source = self.icons[1]
        self.title_text = self.title_texts[1]
        self.body_text = roboprinter.lang.pack['FT_ZOffset_Wizard']['Finish']['Body'] + str(self.updated_offset)
            


        
        
        

