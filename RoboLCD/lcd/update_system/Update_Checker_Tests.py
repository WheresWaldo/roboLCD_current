import unittest
from RoboLCD.lcd.update_system.Update_Interface import Update_Interface
from RoboLCD.lcd.update_system.Update_System import Update_System

class Update_Checker_Test(unittest.TestCase):

    def name_wrapper(function):
        def print_name(*args, **kwargs):
            print("Executing: " + str(function.__name__))
            result = function(*args, **kwargs)
            return result
        return print_name

    @name_wrapper
    def test_get_updates(self):
        uc = Update_Interface()
        updates = uc.get_updates()

        #check that the update server is on
        if updates == []:
            print("Update Server is not on")
        else:
            print("Update Server is on or used to be on")

        #Check if there are 7 keys in the first entry update dictionary
        self.assertEqual(len(updates[0]), 7 )

        #check that the seven keys are present in every update dictionary
        catagories = ['version','force', 'name', 'url', 'checksum', 'playbook', 'installed']
        for item in catagories:
            for update in updates:
                if type(update) is dict:
                    self.assertIn(item, update)

    #@name_wrapper
    @unittest.skip("This will reboot the machine if it goes through")
    def test_select_update(self):
        uc = Update_Interface()
        updates = uc.get_updates()
        import json
        self.assertEqual(uc.select_update(json.dumps(updates[0])), True)

    #This test makes the button list for all available updates
    def test_get_update_buttons(self):
        update_system = Update_System()
        buttons = update_system.make_buttons()

        #get updates
        uc = Update_Interface()
        updates = uc.get_updates()

        self.assertEqual(len(buttons), len(updates))


if __name__ == '__main__':
    unittest.main()