import kivy
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen, NoTransition
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelHeader
from kivy.core.window import Window
from kivy.uix.button import Button
from mainscreen_tabs import FilesTab

Window.size = (800, 480)


class MainScreen(Screen):
    # Represents the main screen template with 3 buttons on top bar: Files, Printer, and Settings
    # Controller of MainScreen state
    pass


class FilesPanel(TabbedPanelHeader):
    content = FilesTab()


class RoboScreenManager(ScreenManager):
    pass


class RoboLcdApp(App):
    def build(self):
        sm = RoboScreenManager(transition=NoTransition())
        sm.add_widget(MainScreen(name='main'))
        return sm


if __name__ == '__main__':
    RoboLcdApp().run()
