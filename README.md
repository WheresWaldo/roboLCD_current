# Change Log 1.11.0

### Major Changes
 - Filament Change/Load, Z-Offset, and Fine Tune Z-Offset wizards changed to support dual extrusion
 - The Preheat Wizard now has profiles for Dual Extrusion as well as profiles for single nozzles
 - Motor Controls will now change the Extruder page if it is in dual extrusion mode
 - Motor Controls will kill all heaters if the user backs out of the wizard.
 - Z-Offset wizard will no longer reset the EEPROM every time it is set. It will reset M206 and M851 only
 - Z-Offset will now put the nozzle closer to the bed, users no longer have to hit up many times
 - If a user backs out of the Z-Offset wizard, their Z-Offset will be set back to what it was.
 - All Wizards are put into their own folder and use a new type of Back Button that increases flow control for the programmer.
 - All Wait screens will not call their callback functions if the user backs out. [Bug Fix]
 - Added PID tuning wizard, This wizard can be used to tune any heater. 
 - FTZO will wait to reach the nozzles target temperature before continuing with the wizard.
 - FTZO has updated speeds so lines get put down faster
 - FTZO will send the G36 command for setting up the printer
 - FTZO has a new Circles mode that draws circles on the bed
 - FTZO will now conform to the size of the bed set in Octoprint
 - FTZO has a changed layout that allows more control over the process for the user.
 - Wifi password obfuscation
 - QR code obfuscation for access control


### Minor Changes
 - PConsole no longer uses the regular expression library to get values from the EEPROM. It now will disassemble the M Command into a dictionary of the values it finds
 - PConsole has an Observer in it now that will allow programs to register callbacks when an EEPROM variable is updated.
 - EEPROM will now show a custom edit range for each value. (Accelerations needs a +100 button but the Z-Offset does not.)
 - Foundation for Dual Extrusion software
 - PID tuner options can be changed with an edit of the loaded language pack. (Target temp, cycle count)
 - Filament loading screen will turn off the heaters if it is backed out of unless the printer is printing.
 - Wizards will now display "Loading..." when pressed.
 - Added a timeout to the update system
 - Added the "depth" tag to the update system so update packages do not download the repository .git folder. This results in very small packages to download
 - Disabled EEPROM during print to avoid a bed crash.
 - USB will now warn the user if the USB drive is unsupported or unmounted
 - Moved Z-Offset capture point to X8.00 Y30.00
 

# Change Log 1.10.0

### Major Changes
 - File System Redesign
    - Sort By Alphabet, Size, Date, or Type
        - Sorting by size will result in each file listing their size
        - Any other sorting will show the date the file was added
    - Users can now Copy, Move, or Delete multiple files and folders at once on USB or Local Files
    - STL and Hex files added to the file view
    - SLicer Wizard and Firmware wizard will be activated when selecting an STL or Hex file
    - USB and Local Files will now show their Used / Total Space on the drive.
    - Meta Data will load when a file is selected for the first time. Then it will be saved for future use
    - Browsing Files is now faster

### Minor Changes
 - Octoprint
    - Changed FileSystem to load Hex Files correctly on the Web Dash
 - Meta-Reader
    - Changed File Analysis so it did not choke on folders without the 'children' catagory 
 - RoboLCD
    - Connection screens will now reflect the realtime connection information (Reset Connction, Bed Disconnect, Mainboard Disconnect)
    - Filament change will now push material through the nozzle before starting the retraction move
    - Added 'F3000' to Raise Z option in motor controls so it would rise at an acceptable speed instead of the last speed given to the printer
    - Fixed Network Title. It used to say Wizards
    - Fixed the Error box starting up with a solid White image.
    - Fixed up and down buttons getting stuck on the File Screen
    - Fixed Keyboard bug that would keep the keyboard up when an error occured
    - Tool monitor will now show one decimal place. Graphical errors occured when showing two or more decimal places

# Change Log 1.9.0
 - Motor Control redesign
    - Added Motors Off 
    - Added an Extruder Page to control the extruder controls seperately
    - Added ability to heat the extruder from the extruder controls
 - Preheat Wizard
    - Added a feature to add custom Preheat settings
    - Added to the Fine Tune ZOffset Wizard, Change/Load Filament Wizard, Slicer Wizard. You can pick a custom heat for these wizards now
    - Added a Feature to edit/delete any preset
 - Z-Offset Wizard
    - Added in an extra 0.05mm
    - Z-Offset is now measured from the corner
 - Confirmation Screens
    - Added Confirmation screen to Reset EEPROM, Shutdown/Reboot, Reset Connection, and Delete File/Folder
 - Slicer Wizard
    - Added Brim and Raft Support
    - Added Supports from buildplate and everywhere
    - Added the ability to choose the temperature to print with
    - Added Fans on/off functionality
 - Added english.yaml file, which holds all the text for the program
 - Refactored Z-Offset Wizard to use template screens.
    - This change was to fit more language on the screen and auto adjust text as needed.
 - Added a kivy widget that auto adjusts image/text combos
 - Added a workflow to execute a function when backing out of a screen
 - Various text changes
 - Various Icon Changes
 - Bugfix
    - Fixed a bug that caused Anyone with dual extruders on the R2 to crash the screen during the Z-Offset Wizard
    - Fixed bug for disconnecting during an active print, the error message said "printing". It will not populate the correct error


# Change Log 1.8.0
 - Added a Web Cam Toggle Button

# Change Log 1.7.0
 - Print Tuning redesign
    - While printing print tuning will be shown, while not printing only fan controls will be shown
 - New Utilities Functions
    - Motors can be disengaged under Utilities >> Options >> Motors Off
    - You can now reset the connection to the printer at any time through the Utilities >> Option >> Connection tool 
    - Firmware Update has been moved to Options
 - Printer Status Redesign
    - New Non Blocking Error Messages
    - Temperature Controls and Motor Controls have been moved to the printer status screen
    - While Printing the screen will now show elapsed time and estimated time remaining
    - Added a progress bar
 - New Wizard Fine Tune Z Offset
 - New Wizard Bed Level Calibration (R2 Only)
 - fixed up and down buttons to have correctly sized elements
 - various language edits
 - Filament Load/Change will not mess with temperature while printing, it will also set the E-Steps back to where they were
 - Onboard sliced files will now be appended with meta data instead of saved directly with meta data


# Setup
If you want to install this repo:

### if you do not already have RoboLCD on the machine go ahead and clone it
```
git clone https://github.com/Robo3D/RoboLCD.git
```
### if you do have RoboLCD  on the machine pull the updates
```
# Make sure you are in the RoboLCD Folder
cd RoboLCD
git pull
```

### Switch to this branch
```
# Make sure you are in the RoboLCD Folder
cd RoboLCD
git checkout [branch name]
```

### install RoboLCD in develop mode
```
source ~/oprint/bin/activate
# Make sure you are in the RoboLCD Folder
cd ~/RoboLCD
python setup.py develop
```
### restart octoprint and pull up the log 
```
sudo service octoprint restart & tail -f ~/.octoprint/logs/octoprint.log
```



