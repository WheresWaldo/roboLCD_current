import kivy
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, NoTransition
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelHeader
from kivy.core.window import Window
from kivy.uix.button import Button
from mainscreen import MainScreen, MainScreenTabbedPanel, FilesTab, PrinterStatusTab, SettingsTab

Window.size = (800, 480)


class RoboScreenManager(ScreenManager):
    """
    Root widget
    """
    pass


class RoboLcdApp(App):
    def build(self):
        # Instantiate Screen Manager and add a child widget-- the Main Screen
        # Root widget is RoboScreenManager
        sm = RoboScreenManager(transition=NoTransition())
        sm.add_widget(MainScreen(name='main'))
        return sm


if __name__ == '__main__':
    RoboLcdApp().run()
