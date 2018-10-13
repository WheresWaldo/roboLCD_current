# -*- coding: utf-8 -*-
# @Author: Matt Pedler
# @Date:   2017-10-11 12:11:58
# @Last Modified by:   Matt Pedler
# @Last Modified time: 2018-02-21 18:08:11
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
from RoboLCD.lcd.common_screens import Picture_Button_Screen, Wait_Screen, Override_Layout,Picture_Button_Screen_Body, Button_Screen, Info_Screen
from RoboLCD.lcd.Language import lang


class Z_Offset_Workflow(object):
    """docstring for Z_Offset_Workflow"""
    def __init__(self, selected_tool, callback, update_z_offset, back_button, group, **kwargs):
        super(Z_Offset_Workflow, self).__init__()
        self.model = roboprinter.printer_instance._settings.get(['Model'])
        self.selected_tool = selected_tool
        self.callback = callback
        self.update_z_offset = update_z_offset
        self.bb = back_button
        self.group = group
        self.old_z_offset = {}

        self.z_pos_init = 20.00
        self.z_pos_end = 0.0

        #position callback variables
        self.old_xpos = 0
        self.old_ypos = 0
        self.old_zpos = 0

        self.preparing_printer_screen()

    def cleanup(self):
        Logger.info("Deleting Z Offset Workflow")
        self.bb = ''
        del_list = []
        for self_var in self.__dict__:
            del_list.append(self_var)
            self.__dict__[self_var] = ''
        for self_var in del_list:
            #Logger.info("Deleting " + str(self_var))
            del self.__dict__[self_var]
        del self

    def preparing_printer_screen(self, *args):
        """Loading Screen
            Displays to user that Z Axis is moving """

        #Prepare screen
        title = lang.pack['ZOffset_Wizard']['Z_14']
        self.wait_screen = Wait_Screen(self.check_temp_and_change_screen, '',lang.pack['ZOffset_Wizard']['Auto_Next'], watch_action=True)
        self.wait_screen.change_screen_actions = self.restore_z_offset
        self.wait_screen.update = self.wait_screen_skip_action
        self.bb.make_screen(self.wait_screen,
                         title,
                         option_function='no_option')

        Logger.info("Preparing Printer")
        #query the EEPROM
        pconsole.query_eeprom()
        #Wait a little bit for the EEPROM to be captured, then prepare printer
        Clock.schedule_once(self._prepare_printer, 0.5)

    def wait_screen_skip_action(self):
        Logger.info("Prepare Printer back action!")
        roboprinter.printer_instance._printer.commands('M107')
        self.bb.back_function_flow()

    def restore_z_offset(self):
        roboprinter.printer_instance._printer.commands('M107')
        self.wait_screen.changed_screen = True
        if self.selected_tool in self.old_z_offset:
            Logger.info("User backed out, restoring Z Offset")
            write_zoffset = 'M206 Z' + str(self.old_z_offset[self.selected_tool])
            save_to_eeprom = 'M500'
            roboprinter.printer_instance._printer.commands([write_zoffset, save_to_eeprom])
            Logger.info("Restored Z Offset to: " + str(self.old_z_offset[self.selected_tool]))
        else:
            Logger.info("User backed out but there is no old Z Offset data")



    def check_temp_and_change_screen(self, *args, **kwargs):
        temps = roboprinter.printer_instance._printer.get_current_temperatures()

        #find the temperature
        extruder_temp = 0 #initialize the variable so the function does not break.
        if self.selected_tool in temps:
            extruder_temp = temps[self.selected_tool]['actual']
        else:
            Logger.info("Cannot find temperature for: " + str(self.selected_tool))

        if extruder_temp < 100:
            self.offset_adjustment_screen()
        else:
            self.temperature_wait_screen()

    def temperature_wait_screen(self, *args):
        title = roboprinter.lang.pack['ZOffset_Wizard']['Wait']
        back_destination = roboprinter.robo_screen()

        layout = Z_Offset_Temperature_Wait_Screen(self.selected_tool, self.offset_adjustment_screen)

        self.bb.make_screen(layout,
                         title,
                         option_function='no_option')

        Logger.info("Temperature Wait Screen Activated")



    def offset_adjustment_screen(self, *args):

        #turn off fan
        roboprinter.printer_instance._printer.commands('M106 S0')
        """
        Instructions screen
        """
        title = roboprinter.lang.pack['ZOffset_Wizard']['Z_24']

        Logger.info("Updated Zoffset is: " + str(self.z_pos_init))

        layout = Z_Offset_Adjuster(self.capture_z_offset)

        self.bb.make_screen(layout,
                         title,
                         option_function='no_option')

    #This is where the workflow ends. This will show a screen saying that the z pos is being saved,
    #then it will go back to the parent workflow.
    def capture_z_offset(self, *args):

        #show an info screen with what the printer is doing.

        layout = Info_Screen(lang.pack['ZOffset_Wizard']['Capturing'], lang.pack['ZOffset_Wizard']['Capture_Offset'])

        self.bb.make_screen(layout,
                         "Please Wait",
                         option_function='no_option')
        layout.update = self.skip_capture


        #run the capture commands
        Clock.schedule_once(self._capture_z_offset, 0.2)

    def skip_capture(self):
        Logger.info("skipping over capture screen")
        self.bb.back_function_flow() 
        

    def _capture_z_offset(self, *args, **kwargs):

        self.z_pos_end = float(self._capture_zpos()) #schema: (x_pos, y_pos, z_pos)
        self.z_pos_end = float(self._capture_zpos()) #runs twice because the first call returns the old position
        Logger.info("ZCapture: z_pos_end {}".format(self.z_pos_end))
        self.zoffset = (self.z_pos_end) * -1.00

        #send Z Offset Values
        self.update_z_offset(self.selected_tool, self.zoffset)

        #save Z Offset then return to the parent workflow
        self.end_wizard()




    #####Helper Functions#######
    def _prepare_printer(self, *args, **kwargs):
        # Prepare printer for zoffset configuration

        #select the correct tool
        self.change_tool()

        #kill the extruder
        roboprinter.printer_instance._printer.commands('M104 S0')
        roboprinter.printer_instance._printer.commands('M140 S0')
        roboprinter.printer_instance._printer.commands('M106 S255')

        #save the current ZOffset
        self.old_z_offset[self.selected_tool] =  pconsole.home_offset['Z']

        #Log the current Z-Offset
        Logger.info("Saving the current Z-Offset as: " + str(self.old_z_offset[self.selected_tool]))

        #set the ZOffset to zero
        Logger.info("Setting the Z-Offset to 0!")
        roboprinter.printer_instance._printer.commands('M206 Z0.00')
        roboprinter.printer_instance._printer.commands("M851 Z0.00")

        #save the new offset
        roboprinter.printer_instance._printer.commands('M500')

        #home then move the head into the correct position
        Logger.info("Homing Printer")
        roboprinter.printer_instance._printer.commands('G28')

        bed_x = 8.00
        bed_y = 30.00

        roboprinter.printer_instance._printer.commands('G1 X' + str(bed_x) + ' Y' + str(bed_y) +' F10000')

        #on the R2 we can safely move closer to the nozzle, while on the C2 we cannot
        if self.model == "Robo R2":
            roboprinter.printer_instance._printer.commands('G1 Z15 F1500')
        else:
            roboprinter.printer_instance._printer.commands('G1 Z20 F750')

        roboprinter.printer_instance._printer.commands('M114')
        roboprinter.printer_instance._printer.commands('M118 ACTION COMPLETE!')

    def change_tool(self):
        #wait until tool change has happened
        while not pconsole.change_tool(self.selected_tool):
            pass

    def position_callback(self, dt):
        temps = roboprinter.printer_instance._printer.get_current_temperatures()
        pos = pconsole.get_position()
        if pos != False:
            xpos = int(float(pos[0]))
            ypos = int(float(pos[1]))
            zpos = int(float(pos[2]))

            extruder_one_temp = 105

            #find the temperature
            if 'tool0' in temps.keys():
                extruder_one_temp = temps['tool0']['actual']

            Logger.info("Counter is at: " + str(self.counter))
            #check the extruder physical position
            if self.counter > 25 and  xpos == self.old_xpos and ypos == self.old_ypos and zpos == self.old_zpos:
                if self.sm.current == 'zoffset[1]':
                    if extruder_one_temp < 100:
                        Logger.info('Succesfully found position')
                        self.offset_adjustment_screen()
                        return False
                    else:
                        self.temperature_wait_screen()
                        return False
                else:
                    Logger.info('User went to a different screen Unscheduling self.')
                    #turn off fan
                    roboprinter.printer_instance._printer.commands('M106 S0')
                    return False

            #if finding the position fails it will wait 30 seconds and continue
            self.counter += 1
            if self.counter > 60:
                if self.sm.current == 'zoffset[1]':
                    Logger.info('could not find position, but continuing anyway')
                    if extruder_one_temp < 100:
                        self.offset_adjustment_screen()
                        return False
                    else:
                        self.temperature_wait_screen()
                        return False
                else:
                    Logger.info('User went to a different screen Unscheduling self.')
                    #turn off fan
                    roboprinter.printer_instance._printer.commands('M106 S0')
                    return False

            #position tracking
            self.old_xpos = xpos
            self.old_ypos = ypos
            self.old_zpos = zpos


    def _capture_zpos(self):
        """gets position from pconsole. :returns: integer"""
        Logger.info("ZCapture: Init")
        p = pconsole.get_position()
        while p == False:
            p = pconsole.get_position()

        Logger.info("ZCapture: "+ str(p))
        return p[2]

    def _save_zoffset(self, *args):
        #turn off fan
        roboprinter.printer_instance._printer.commands('M106 S0')
        #write new home offset to printer
        write_zoffset = 'M206 Z' + str(self.zoffset)
        save_to_eeprom = 'M500'
        roboprinter.printer_instance._printer.commands([write_zoffset, save_to_eeprom])
        #pconsole.home_offset['Z'] = self.zoffset


    def end_wizard(self, *args):
        #turn off fan
        self._save_zoffset()
        roboprinter.printer_instance._printer.commands('M106 S0')

        #capture the offset
        from RoboLCD.lcd.wizards.FTZO.console_watcher import Console_Watcher
        Console_Watcher(self.wait_for_update)

        pconsole.query_eeprom()
        roboprinter.printer_instance._printer.commands("M118 ACTION COMPLETE!")
        Clock.schedule_interval(self.wait_for_update, 0.5)


    def wait_for_update(self, *args, **kwargs):

        if pconsole.home_offset['Z'] != 0:
            self.callback()
            return False



class Z_Offset_Adjuster(BoxLayout):
    i_toggle_mm = ListProperty(['Icons/Manual_Control/increments_3_1.png',
                                'Icons/Manual_Control/increments_3_2.png',
                                'Icons/Manual_Control/increments_3_3.png']
                              )
    s_toggle_mm = ListProperty([roboprinter.lang.pack['ZOffset_Wizard']['zero_five'],
                                roboprinter.lang.pack['ZOffset_Wizard']['one_zero'],
                                roboprinter.lang.pack['ZOffset_Wizard']['two_zero']]
                              )
    f_toggle_mm = ListProperty([0.05, 0.1, 0.2])
    toggle_mm = NumericProperty(1)

    callback = ObjectProperty(None)

    def __init__(self, callback):
        super(Z_Offset_Adjuster,self).__init__()
        self.callback = callback

    def toggle_mm_z(self):

        toggle = self.toggle_mm + 1
        if toggle > 2:
            self.toggle_mm = 0
        else:
            self.toggle_mm += 1

        Logger.info(self.s_toggle_mm[self.toggle_mm])

    def _jog(self, direction):
        # determine increment value
        increment = direction * self.f_toggle_mm[self.toggle_mm]
        jogger = {'z': increment}
        printer_jog.jog(desired=jogger, speed=1500, relative=True)


#TODO Refactor this screen to say which extruder it's waiting on
class Z_Offset_Temperature_Wait_Screen(FloatLayout):

    body_text = StringProperty(roboprinter.lang.pack['ZOffset_Wizard']['Cooldown'])
    temperature = StringProperty("999")
    bed_temp = StringProperty("999")


    def __init__(self, selected_tool, callback):
        super(Z_Offset_Temperature_Wait_Screen, self).__init__()

        self.selected_tool = selected_tool
        #setup callback
        model = roboprinter.printer_instance._settings.get(['Model'])
        if model == "Robo R2":
            self.body_text = roboprinter.lang.pack['ZOffset_Wizard']['Cooldown']
            Clock.schedule_interval(self.temp_callback_R2, 0.5)
        else:
            Clock.schedule_interval(self.temperature_callback, 0.5)

        self.callback = callback
        self.changed_screen = False

    def change_screen_event(self):
        self.changed_screen = True

    def temperature_callback(self,dt):
        temps = roboprinter.printer_instance._printer.get_current_temperatures()
        position_found_waiting_for_temp = False

        #get current temperature
        if self.selected_tool in temps.keys():
            temp = temps[self.selected_tool]['actual']
            self.temperature = str(temp)

            if temp < 100:
                position_found_waiting_for_temp = True
                #go to the next screen
                if not self.changed_screen:
                    self.callback()
                return False

        if self.changed_screen:
            return False


    def temp_callback_R2(self, dt):
        temps = roboprinter.printer_instance._printer.get_current_temperatures()
        position_found_waiting_for_temp = False
        bed = 100
        #get current temperature
        if self.selected_tool in temps.keys():
            temp = temps[self.selected_tool]['actual']
            self.temperature = str(temp)

        if 'bed' in temps.keys():
            bed = temps['bed']['actual']
            self.bed_temp = str(bed)

            if temp < 100 and bed < 60:
                position_found_waiting_for_temp = True
                #go to the next screen
                if not self.changed_screen:
                    self.callback()
                return False

        if self.changed_screen:
            return False
