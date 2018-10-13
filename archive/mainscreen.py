from kivy.uix.screenmanager import Screen
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelHeader
from kivy.uix.label import Label


class MainScreen(Screen):
    """
    Represents the the main screen template with 3 tab buttons on the top bar: Files, Printer, and Settings
    """
    pass


class MainScreenTabbedPanel(TabbedPanel):
    """
    Represents the tabbed panels. Handles toggling between FilesTab, PrinterStatusTab and SettingsTab
    """
    pass


class FilesTab(TabbedPanelHeader):
    """
    Represents the Files tab header and dynamic content
    """
    pass


class PrinterStatusTab(TabbedPanelHeader):
    """
    Represents the Printer Status tab header and dynamic content
    """
    pass


class SettingsTab(TabbedPanelHeader):
    """
    Represents the Settings tab header and dynamic content
    """
    pass


class PrinterStatusContent(Label):
    pass


class FilesContent(Label):
    pass


class SettingsContent(Label):
    pass
