#python
import json
import traceback
import requests

#kivy
from kivy.logger import Logger

class Update_Interface(object):

    def __init__(self):
        super(Update_Interface,self).__init__()
        pass

    #returns list of available updates
    def get_updates(self):
        try:
            json_pack = requests.get('http://127.0.0.1:8888/state', timeout=0.5)
            Logger.info(str(json_pack))
            Logger.info(str(json_pack.text))
            if json_pack.status_code == 200:
                return json.loads(str(json_pack.text))
            else:
                return False

        except requests.exceptions.ConnectTimeout as e:
            # we don't need to log that it timed out
            return False
        except Exception as e:
            Logger.info("!!!!!!!!!!!!!!! Error: " + str(e))
            traceback.print_exc()
            return False

    def select_update(self, update):
        try:
            # `json = update` will automatically translate dictionary into json and set the correct headers so that receiving end knows content=application/json 
            response = requests.post('http://127.0.0.1:8888/update', timeout=0.5, json=update)

            #if the upload went through then return true, if not return false
            if int(response.status_code) == 200:
                return True
            else:
                return False
        except requests.exceptions.ConnectTimeout as e:
            # we don't need to log that it timed out
            return False
        except Exception as e:
            Logger.info("!!!!!!!!!!!!!!! Error: " + str(e))
            traceback.print_exc()
            return False



    def close(self):
        self.write_update.remove()
