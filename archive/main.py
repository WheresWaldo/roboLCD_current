from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen, NoTransition

class MainScreen(Screen):
	# Represents the main screen template with 3 buttons on top bar: Files, Printer, and Settings
	pass

class BackButtonScreen(Screen):
	# Represents the template for the screens that branch out from the MainScreen and need a backbutton
	pass

class NoHeaderScreen(Screen):
	# Represents the template for screens with no header bars. User clicks a Button (e.g. Cancel or OK) to return to Main Screen or Previous Screen
	pass

class RoboScreenManager(ScreenManager):
	# ROOT WIDGET
	# Screen manager for Robo LCD
	# Generates dynamic screens when they stem off MainScreen
	def generate_screen(self, template, content, previous):
		"""
		Dynamically creates a screen. Will be used to dynamically generate non-MainScreen

		Notes on parameters-
			Template: visual screen structure
			Content: parse and populate properties with contents
			Previous: [template]
				'go back' call to action will go back to that screen. This is important because it doesn't seem like you can manually remove screen in the stack. The only method I have found that can remove screen is .switch_to(screen,**options). Maybe the workflow is such that when a user leaves the MainScreen, the generate_screen() is called and the new screen is ported into  .switch_to(). 
					s = generate_screen(*args)
					.switch_to(s)
				The 'go back' cta will be populated by Previous.
					Button:
						name: 'go back'
						on_release: .switch_to(previous)
		"""
		pass

class RoboLcdApp(App):
	def build(self):
		sm = RoboScreenManager(transition=NoTransition())
		sm.add_widget(MainScreen(name='main'))
		sm.add_widget(BackButtonScreen(name='back'))
		sm.add_widget(NoHeaderScreen(name='noheader'))
		return sm 

if __name__ == '__main__':
	RoboLcdApp().run()