# -*- coding: utf-8 -*-
# @Author: Matt Pedler
# @Date:   2017-09-18 15:07:34
# @Last Modified by:   Matt Pedler
# @Last Modified time: 2017-10-27 13:14:45
import yaml
import os



class Language():
    def __init__(self, language):
        self.pack = None
        self.load_language(language)
        self.current_lang = 'en'
        

    def load_language(self, language):
        acceptable_languages = {'en': "Language_Packs/english.yaml",
                                'sp': "Language_Packs/spanish.yaml",
                                'gib': 'Language_Packs/redo.yaml'}

        if language in acceptable_languages:
            _dir = os.path.dirname(__file__)
            yaml_path = os.path.join(_dir, acceptable_languages[language])
            with open(yaml_path, 'r') as file:
                self.pack = yaml.load(file)

            self.current_lang = language


    def reload_language(self, language):
        self.load_language(language)

lang = Language("en")

                  