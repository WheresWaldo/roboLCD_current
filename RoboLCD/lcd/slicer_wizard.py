# -*- coding: utf-8 -*-
# @Author: Matt Pedler
# @Date:   2017-10-03 12:31:38
# @Last Modified by:   Matt Pedler
# @Last Modified time: 2018-03-08 11:48:21
from kivy.uix.button import Button
from kivy.properties import StringProperty, NumericProperty, ObjectProperty, BooleanProperty
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.uix.togglebutton import ToggleButton
from RoboLCD import roboprinter
from functools import partial
from kivy.logger import Logger
from kivy.clock import Clock
from pconsole import pconsole
import thread
from connection_popup import Error_Popup, USB_Progress_Popup
import os
import tempfile
import traceback
import shutil
import subprocess
from scrollbox import Scroll_Box_Even
from common_screens import Button_Group_Observer, OL_Button, Override_Layout
from RoboLCD.lcd.wizards.preheat_wizard.preheat_overseer import Preheat_Overseer

USB_DIR = '/home/pi/.octoprint/uploads/USB'
FILES_DIR = '/home/pi/.octoprint/uploads'
TEMP_DIR = '/tmp/stl'
CURA_DIR = '/home/pi/.octoprint/slicingProfiles/cura'

class Slicer_Wizard(FloatLayout):

    def __init__(self,file_data, back_button_callback):
        super(Slicer_Wizard, self).__init__()

        #make default meta data
        self.meta = {
            'layer height' : '--',
            'layers' : '--',
            'infill' : '--',
            'time' : {'hours': str(0), 
                      'minutes': str(0),
                      'seconds': str(0)
                      }
        }
        #make sure the tmp directory exists
        self.search_for_temp_dir()

        self.sm = roboprinter.robosm
        self.oprint = roboprinter.printer_instance
        self.back_button_callback = back_button_callback
        self.file_data = file_data

        #show the confirmation screen

        self.show_confirmation_screen()

    def show_confirmation_screen(self):
        screen_name = "slicing wizard"
        title = roboprinter.lang.pack['Slicer_Wizard']['Confirmation']['Title']
        back_destination = "File_Explorer"
        layout = STL_Confirmation_Screen(self.choose_overrides, self.file_data['name'])
        roboprinter.back_screen(name = screen_name, 
                                title = title, 
                                back_destination=back_destination, 
                                content=layout
                                )

    def search_for_temp_dir(self):
        if not os.path.exists(TEMP_DIR):
            os.makedirs(TEMP_DIR)
            Logger.info("Made temp directory for slicing")

    def choose_overrides(self):
        screen_name = 'slicer_overrides'
        title = roboprinter.lang.pack['Slicer_Wizard']['Overrides']['Title']
        back_destination = self.sm.current
        layout = Override_Page(self.slice_stl)

    
    def slice_stl(self, overrides):
        #get the profile from octoprint
        self.progress_pop =  USB_Progress_Popup(roboprinter.lang.pack['Slicer_Wizard']['Progress']['Sub_Title'] + self.file_data['name'], 1)
        self.progress_pop.show()
        self.stl_name = self.file_data['name'].replace(".stl", "")
        self.stl_name = self.stl_name.replace(".STL", "")
        self.stl_name = self.stl_name + ".gcode"
        self.stl_path = roboprinter.printer_instance._file_manager.path_on_disk('local', self.file_data['path'])
        self.overrides = overrides

        Clock.schedule_once(self.start_slice, 0.1)

    def start_slice(self,dt):
        profiles = roboprinter.printer_instance._slicing_manager.all_profiles('cura', require_configured=False)
        if 'robo' in profiles:
            #start slice
            self.temp_path = TEMP_DIR + "/" + self.stl_name
            Logger.info("Starting Slice")
            Logger.info(self.overrides)
            roboprinter.printer_instance._slicing_manager.slice('cura', 
                                                                self.stl_path, 
                                                                self.temp_path, 
                                                                'robo', 
                                                                self.sliced, 
                                                                overrides=self.overrides,
                                                                on_progress = self.slice_progress)
        else:
            #put our profile in the profile list
            profile_path = os.path.dirname(os.path.realpath(__file__))
            profile_path += '/slicer_profile/robo.profile'

            if os.path.isfile(profile_path):
                #copy a backup of the profile to the default profile directory
                shutil.copyfile(profile_path, CURA_DIR + '/robo.profile')
                
                #if the backup exists and we have tried restoring it 5 times give up and error out
                if dt < 5:
                    Logger.info('Restarting the slice, Rec Depth = ' + str(dt+1))
                    self.start_slice(dt+1)
                else:
                    ep = Error_Popup(roboprinter.lang.pack['Slicer_Wizard']['Error']['Profile']['Sub_Title'], roboprinter.lang.pack['Slicer_Wizard']['Error']['Profile']['Body'],callback=partial(roboprinter.robosm.go_back_to_main, tab='printer_status_tab'))
                    ep.show()
            #if the backup does not exist then error out
            else:
                Logger.info('Slicer Error: Path Does not exist')
                ep = Error_Popup(roboprinter.lang.pack['Slicer_Wizard']['Error']['Profile']['Sub_Title'], roboprinter.lang.pack['Slicer_Wizard']['Error']['Profile']['Body'],callback=partial(roboprinter.robosm.go_back_to_main, tab='printer_status_tab'))
                ep.show()
            

    def sliced(self, **kwargs):
        Logger.info(kwargs)
        if '_error' in kwargs:
            #doing this will get rid of graphical errors. Kivy does not like being managed from an outside thread.
            Logger.info(str(kwargs['_error']))
            Clock.schedule_once(self.error_pop, 0.01)
        elif '_analysis' in kwargs:
            #initialize meta data
            ept = 0
            lh = str(self.overrides['layer_height'])
            infill = str(self.overrides['fill_density'])
            if 'estimatedPrintTime' in kwargs['_analysis']:
                ept = kwargs['_analysis']['estimatedPrintTime']
            #save meta data
            self.meta = {
                'layer height' : lh,
                'infill' : infill,
                'time' : ept
            }

            Logger.info("finished Slice")
            self.progress_pop.hide()
            #after slicing ask the user where they want the file to be saved at
            Clock.schedule_once(self.save_file, 0.01)

        else:
            Logger.info("finished Slice")
            self.progress_pop.hide()
            #after slicing ask the user where they want the file to be saved at
            Clock.schedule_once(self.save_file, 0.01)


    def error_pop(self, dt, *args, **kwargs):
        self.progress_pop.hide()
        
        os.remove(self.temp_path)
        ep = Error_Popup(roboprinter.lang.pack['Slicer_Wizard']['Error']['Slice']['Sub_Title'], roboprinter.lang.pack['Slicer_Wizard']['Error']['Slice']['Body'],callback=partial(roboprinter.robosm.go_back_to_main, tab='printer_status_tab'))
        ep.show()
     # This takes a number in seconds and returns a dictionary of the hours/minutes/seconds
    def parse_time(self, time):
        m, s = divmod(time, 60)
        h, m = divmod(m, 60)

        time_dict = {'hours': str(h),
                     'minutes': str(m),
                     'seconds': str(s)
                     }

        return time_dict


    # this function exists because calling the Save_File class directly from the sliced function resulted in Graphical issues
    # Setting a clock to call this function fixed the graphical issues. I believe it is because the sliced function gets called
    # by the slicing manager thread, and graphical issues do present themselves when calling kivy objects outside the thread
    # they are created in.
    def save_file(self, dt):
        Logger.info('Saving data ' + self.temp_path + ' along with the meta data: ' + str(self.meta))
        #save the file
        self.back_button_callback(self.temp_path, self.meta, back_to_name='fans_page')

    def slice_progress(self, *args, **kwargs):
        if '_progress' in kwargs:
            #Logger.info(str(kwargs['_progress']))
            self.current_progress = kwargs['_progress']
            #Just trying to avoid graphical issues
            Clock.schedule_once(self.get_progress, 0)
            

    def get_progress(self, dt, *args, **kwargs):
        self.progress_pop.update_progress(self.current_progress)
    

class STL_Confirmation_Screen(GridLayout):
    button_function = ObjectProperty(None)
    file_name = StringProperty('')
    button_state = BooleanProperty(False)

    def __init__(self, function, file_name):
        super(STL_Confirmation_Screen, self).__init__()
        self.button_function = function
        self.file_name = file_name
        if roboprinter.printer_instance._printer.is_ready() and not roboprinter.printer_instance._printer.is_printing() and not roboprinter.printer_instance._printer.is_paused():
            self.button_state = False
        else:
            self.button_state = True

class Override_Page(object):

    def __init__(self, slice_callback):
        super(Override_Page, self).__init__()
        #initialize properties
        self._support = 'none'
        self._platform_adhesion = 'none'
        self._first_layer_width = 300.0
        self._layer_height = 0.15
        self._infill = 20
        self._fans = True

        #variable for calling once the user is done setting overrides
        self.slice_callback = slice_callback
        self.set_support()

        

    ####################################Property Settings#########################

    #These are the class settings that will eventually become overrides

    @property
    def support(self):
        Logger.info("Getting support")
        return self._support

    @support.setter
    def support(self, value):
        self._support = value
        Logger.info("setting support to: " + str(self._support))

    @property
    def platform_adhesion(self):
        Logger.info("Getting platform_adhesion")
        return self._platform_adhesion

    @platform_adhesion.setter
    def platform_adhesion(self, value):
        self._platform_adhesion = value
        Logger.info("setting platform_adhesion to: " + str(self._platform_adhesion))
        if self._platform_adhesion != 'none':
            self._first_layer_width = 100.0
        else:
            self._first_layer_width = 300.0

    @property
    def layer_height(self):
        Logger.info("Getting layer_height")
        return self._layer_height

    @layer_height.setter
    def layer_height(self, value):
        Logger.info("setting layer_height to: "+ str(self._layer_height))
        self._layer_height = value

    @property
    def infill(self):
        Logger.info("Getting infill")
        return self._infill

    @infill.setter
    def infill(self, value):
        Logger.info("setting infill to: " + str(self._infill))
        self._infill = value

    #########################################end Class Properties

    def set_support(self, **kwargs):

        sup_overseer = Button_Group_Observer()

        #functions to alter self.support
        def none(state):
            self.support = 'none'
        def buildplate(state):
            self.support = 'buildplate'
        def everywhere(state):
            self.support = 'everywhere'

        none_button = OL_Button(roboprinter.lang.pack['Slicer_Wizard']['Support']['No_Supports'],
                                "Icons/Slicer wizard icons/No Supports.png",
                                none,
                                enabled = True,
                                observer_group = sup_overseer)

        buildplate_button = OL_Button(roboprinter.lang.pack['Slicer_Wizard']['Support']['Buildplate'],
                                "Icons/Slicer wizard icons/Supports buildplate.png",
                                buildplate,
                                enabled = False,
                                observer_group = sup_overseer)

        everywhere_button = OL_Button(roboprinter.lang.pack['Slicer_Wizard']['Support']['Everywhere'],
                                "Icons/Slicer wizard icons/Supports everywhere.png",
                                everywhere,
                                enabled = False,
                                observer_group = sup_overseer)

        bl = [none_button, buildplate_button, everywhere_button]

        layout = Override_Layout(bl, roboprinter.lang.pack['Slicer_Wizard']['Support']['Body'])
        back_destination = roboprinter.robosm.current
        roboprinter.back_screen(name = 'support_page',
                                title = roboprinter.lang.pack['Slicer_Wizard']['Support']['Title'],
                                back_destination=back_destination,
                                content=layout,
                                cta = self.raft_option,
                                icon = "Icons/Slicer wizard icons/next.png")

    
    def raft_option(self):

        raft_bgo = Button_Group_Observer()

        def none(state):
            self.platform_adhesion = 'none'
        def raft(state):
            self.platform_adhesion = 'raft'
        def brim(state):
            self.platform_adhesion = 'brim'

        none_button = OL_Button(roboprinter.lang.pack['Slicer_Wizard']['Raft_Support']['no_raft'], 
                                "Icons/Slicer wizard icons/No Supports.png", 
                                none,
                                enabled = False,
                                observer_group = raft_bgo)
        raft_button = OL_Button(roboprinter.lang.pack['Slicer_Wizard']['Raft_Support']['raft'], 
                                "Icons/Slicer wizard icons/rafts_1.png", 
                                raft,
                                enabled = True,
                                observer_group = raft_bgo)

        brim_button = OL_Button(roboprinter.lang.pack['Slicer_Wizard']['Raft_Support']['brim'], 
                                "Icons/Slicer wizard icons/brim.png", 
                                brim,
                                enabled = False,
                                observer_group = raft_bgo)

        bl = [none_button, raft_button, brim_button]

        layout = Override_Layout(bl, roboprinter.lang.pack['Slicer_Wizard']['Raft_Support']['Body'])
        back_destination = roboprinter.robosm.current
        roboprinter.back_screen(name = 'raft and support', 
                                title = roboprinter.lang.pack['Slicer_Wizard']['Raft_Support']['Title'] , 
                                back_destination=back_destination, 
                                content=layout,
                                cta = self.print_quality,
                                icon = "Icons/Slicer wizard icons/next.png")

    def print_quality(self):
        
        bgo_pq = Button_Group_Observer()

        def mm_20(state):
            if state:
                self.layer_height = 0.20
        def mm_15(state):
            if state:
                self.layer_height = 0.15
        def mm_10(state):
            if state:
                self.layer_height = 0.10
        def mm_06(state):
            if state:
                self.layer_height = 0.06

        mm_20_button = OL_Button(roboprinter.lang.pack['Slicer_Wizard']['Print_Quality']['mm_20'], 
                                "Icons/Slicer wizard icons/60px/step1 (1).png", 
                                mm_20, 
                                enabled = False, 
                                observer_group = bgo_pq)
        mm_15_button = OL_Button(roboprinter.lang.pack['Slicer_Wizard']['Print_Quality']['mm_15'], 
                                "Icons/Slicer wizard icons/60px/step2 (1).png", 
                                mm_15, 
                                enabled = True, 
                                observer_group = bgo_pq)
        mm_10_button = OL_Button(roboprinter.lang.pack['Slicer_Wizard']['Print_Quality']['mm_10'], 
                                "Icons/Slicer wizard icons/60px/step3 (1).png", 
                                mm_10, 
                                enabled = False, 
                                observer_group = bgo_pq)
        mm_06_button = OL_Button(roboprinter.lang.pack['Slicer_Wizard']['Print_Quality']['mm_06'], 
                                "Icons/Slicer wizard icons/60px/step4.png", 
                                mm_06, 
                                enabled = False, 
                                observer_group = bgo_pq)

        bl = [mm_20_button, mm_15_button, mm_10_button, mm_06_button]


        layout = Override_Layout(bl, roboprinter.lang.pack['Slicer_Wizard']['Print_Quality']['Body'])
        back_destination = roboprinter.robosm.current
        roboprinter.back_screen(name = 'print quality', 
                                title = roboprinter.lang.pack['Slicer_Wizard']['Print_Quality']['Title'] , 
                                back_destination=back_destination, 
                                content=layout,
                                cta = self.infill_layout,
                                icon = "Icons/Slicer wizard icons/next.png")

    
    def infill_layout(self):
        
        bgo_pq = Button_Group_Observer()

        def p_0(state):
            if state:
                self.infill = 0
        def p_10(state):
            if state:
                self.infill = 10
        def p_25(state):
            if state:
                self.infill = 25
        def p_100(state):
            if state:
                self.infill = 100

        percent_0 = OL_Button(roboprinter.lang.pack['Slicer_Wizard']['Infill']['p_0'], 
                              "Icons/Slicer wizard icons/hollow.png", 
                              p_0, 
                              enabled = False, 
                              observer_group = bgo_pq)
        percent_10 = OL_Button(roboprinter.lang.pack['Slicer_Wizard']['Infill']['p_10'], 
                               "Icons/Slicer wizard icons/10%.png", 
                               p_10, 
                               enabled = True, 
                               observer_group = bgo_pq)
        percent_25 = OL_Button(roboprinter.lang.pack['Slicer_Wizard']['Infill']['p_25'], 
                               "Icons/Slicer wizard icons/25%.png", 
                               p_25, 
                               enabled = False, 
                               observer_group = bgo_pq)
        percent_100 = OL_Button(roboprinter.lang.pack['Slicer_Wizard']['Infill']['p_100'], 
                                "Icons/Slicer wizard icons/100%.png", 
                                p_100, 
                                enabled = False, 
                                observer_group = bgo_pq)

        bl = [percent_0, percent_10, percent_25, percent_100]


        layout = Override_Layout(bl, roboprinter.lang.pack['Slicer_Wizard']['Infill']['Body'])
        back_destination = roboprinter.robosm.current
        roboprinter.back_screen(name = 'infill', 
                                title = roboprinter.lang.pack['Slicer_Wizard']['Infill']['Title'], 
                                back_destination=back_destination, 
                                content=layout,
                                cta = self.choose_material,
                                icon = "Icons/Slicer wizard icons/next.png")

    def choose_material(self):
        
        Preheat_Overseer(end_point=self.collect_heat_settings,
                         name='preheat_wizard',
                         title=roboprinter.lang.pack['Utilities']['Preheat'],
                         back_destination='infill')

    def collect_heat_settings(self, extruder, bed):
        self.print_temperature = [extruder,0,0,0]
        self.print_bed_temperature = bed
        self.set_fans()

    def set_fans(self):

        fan_overseer = Button_Group_Observer()

        def fans_on(state):
            self._fans = True

        def fans_off(state):
            self._fans = False

        on_button = OL_Button(roboprinter.lang.pack['Slicer_Wizard']['Fans']['fan_on'],
                              "Icons/Slicer wizard icons/Fans on.png",
                              fans_on,
                              enabled = True,
                              observer_group = fan_overseer)

        off_button = OL_Button(roboprinter.lang.pack['Slicer_Wizard']['Fans']['fan_off'],
                              "Icons/Slicer wizard icons/Fans off.png",
                              fans_off,
                              enabled = False,
                              observer_group = fan_overseer)

        bl = [on_button, off_button]

        layout = Override_Layout(bl, roboprinter.lang.pack['Slicer_Wizard']['Fans']['Body'])
        back_destination = roboprinter.robosm.current
        roboprinter.back_screen(name = 'fans_page',
                                title = roboprinter.lang.pack['Slicer_Wizard']['Fans']['Title'],
                                back_destination=back_destination,
                                content=layout,
                                cta = self.continue_slicing,
                                icon = "Icons/Slicer wizard icons/next.png")

    def continue_slicing(self):

        overrides = {
                    'layer_height': self.layer_height,
                    'print_temperature': self.print_temperature,
                    'print_bed_temperature': self.print_bed_temperature,
                    'fill_density': self.infill,
                    'support': self.support,
                    'platform_adhesion': self.platform_adhesion,
                    'first_layer_width_factor': self._first_layer_width,
                    'fan_enabled': self._fans,
                    'fan_speed': 100 if self._fans else 0,
                    'fan_speed_max': 100 if self._fans else 0,
                    'fan_full_height': 6.0 if self._fans else -1
                    
                    }
        # add the brim settings to the override
        if self.platform_adhesion == 'brim':
            overrides['skirt_line_count'] = 1
            overrides['skirt_gap'] = False
            overrides['skirt_minimal_length'] = False
            overrides['skirt_gap'] = False
            overrides['brim_line_count'] = 10

        Logger.info(str(overrides))

        self.slice_callback(overrides)