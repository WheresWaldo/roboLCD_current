# -*- coding: utf-8 -*-
# @Author: Matt Pedler
# @Date:   2017-07-14 12:42:48
# @Last Modified by:   Matt Pedler
# @Last Modified time: 2018-01-10 12:15:34
# coding=utf-8

#kivy
from kivy.uix.floatlayout import FloatLayout
from kivy.logger import Logger
from kivy.clock import Clock
from kivy.properties import StringProperty

#python
import yaml
import os
import imp
import requests
from git import Repo
from functools import partial
from shutil import rmtree

#roboLCD
from RoboLCD import roboprinter
from RoboLCD.lcd.connection_popup import Error_Popup, Warning_Popup



class UpdateScreen(FloatLayout):
    installed_version = StringProperty(roboprinter.lang.pack['Update_Printer']['Checking'])
    avail_version = StringProperty(roboprinter.lang.pack['Update_Printer']['Checking'])

    def __init__(self, populate=True, **kwargs):
        super(UpdateScreen, self).__init__()

        self.data_path = roboprinter.printer_instance.get_plugin_data_folder()
        self.repo_info_url = 'https://api.github.com/repos/robo3d/Update_Script/releases'
        self.repo_local_path = self.data_path + '/Update_Script'
        self.updater_path = self.repo_local_path + '/Update_Checker/Update_Checker.py'
        self.repo_remote_path = 'https://github.com/Robo3d/Update_Script.git'
        self.versioning_path = self.data_path + '/roboOS.txt'

        self.printer_model = roboprinter.printer_instance._settings.get(['Model'])

        #populate version numbers when screen gets initiated
        self.populate = populate
        if self.populate:
            Clock.schedule_once(self.populate_values)

    def populate_values(self, *args):
        self.refresh_versions()
        self.refresh_button()

    def refresh_button(self, *args):
        if self.installed_version < self.avail_version and self.avail_version != roboprinter.lang.pack['Update_Printer']['Connection_Error']:
            self.enable_me()
        else:
            self.disable_me()

    def refresh_versions(self, *args):
        """populates self.installed_version && self.avail_version: values are rendered on the UpdateScreen."""
        self.installed_version = self.get_installed_version()
        self.avail_version = self.get_avail_version()
        if self.avail_version == roboprinter.lang.pack['Update_Printer']['Connection_Error'] and self.populate:
            Error_Popup(roboprinter.lang.pack['Update_Printer']['Connect_Error']['Title'], roboprinter.lang.pack['Update_Printer']['Connect_Error']['Body'],callback=partial(roboprinter.robosm.go_back_to_main, tab='printer_status_tab')).show()

    def get_installed_version(self):
        path = self.versioning_path
        if os.path.exists(path):
            with open(path, 'r') as f:
                v = f.readline().strip()
        else:
            with open(path, 'w') as f:
                v = '1.0.3'
                f.write(v)
        return v

    def get_avail_version(self):
        """queries github api for repo's latest release version"""
        try:
            r = requests.get(self.repo_info_url, timeout=5.0)
            code = r.status_code
        except Exception as e:
            r = None
            code = None
        if r and code is 200:
            return self._get_avail_version(r.json())
        else:
            return roboprinter.lang.pack['Update_Printer']['Connection_Error']

    def _get_avail_version(self, r):
        # parse json response for latest release version
        model = 'r2' if self.printer_model == 'Robo R2' else 'c2'
        versions = map(lambda info: info.get('tag_name', '0'), r)
        m_versions = filter(lambda v: model in v, versions)
        if len(m_versions) > 1:
            m_versions.sort()
            avail = m_versions.pop()
        else:
            avail = self.installed_version
        return avail

    def update_updater(self, *args):
        if self.printer_model == 'Robo R2':
            branch = 'r2'
        else:
            branch = 'c2'

        if os.path.exists(self.repo_local_path):
            # start fresh every time to avoid potential corruptions or misconfigurations
            rmtree(self.repo_local_path)
        Repo.clone_from(self.repo_remote_path, self.repo_local_path, branch=branch, depth=1)

    def run_updater(self, *args):
        self.disable_me()
        self.warning = Warning_Popup(roboprinter.lang.pack['Update_Printer']['Loading']['Title'], roboprinter.lang.pack['Update_Printer']['Loading']['Body'])
        self.warning.show()
        execute = lambda funcs, dt: map(lambda f: f(), funcs)
        series = [self.update_updater, self._run_updater]
        Clock.schedule_once(partial(execute, series))

    def _run_updater(self):
        from multiprocessing import Process, Pipe
        import subprocess
        import time

        output_p, input_p = Pipe()
        Update_Checker = imp.load_source('Update_Checker', self.updater_path).Update_Checker
        Logger.info('!!!!UPDATING!!!!')
        p = Process(
            target=Update_Checker,
            args=(
                self.versioning_path,
                (output_p, input_p),
            )
        )
        p.start()
        input_p.close()
        # receive message from updater on update status
        while True:
            try:
                updating = output_p.recv()
                Logger.info('MESSAGE: {}'.format(updating))
            except EOFError:
                break
        if updating:
            # kill parent process Octoprint
            subprocess.call("sudo service octoprint stop".split(' '))
        else:
            p.join()
            self.populate_values()
            self.warning.dismiss()
            Error_Popup(roboprinter.lang.pack['Update_Printer']['No_Update']['Title'], roboprinter.lang.pack['Update_Printer']['No_Update']['Body'],callback=partial(roboprinter.robosm.go_back_to_main, tab='printer_status_tab')).show()

    def disable_me(self):
        self.ids.updatebtn.disabled = True
        self.ids.updatebtn.canvas.ask_update()
        # Clock.schedule_once(self.run_updater)
    def enable_me(self):
        self.ids.updatebtn.disabled = False
        self.ids.updatebtn.canvas.ask_update()

