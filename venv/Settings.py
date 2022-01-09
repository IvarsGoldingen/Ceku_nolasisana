import os
from os.path import exists
from pathlib import Path
import regex as re
import subprocess
import logging

"""
Primitive settings file
Line 1 = file location
2 = number 1
3 = number 2
4 = number 3
"""

# logging
log_formatter = logging.Formatter('%(asctime)s:%(name)s:%(levelname)s:%(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(log_formatter)
stream_handler.setLevel(logging.INFO)
logger.addHandler(stream_handler)

class Settings:

    FILE_NAME = "settings"
    FILE_EXT = "txt"
    FILE_LOC = "C:\Ceki_settings"
    FILE_PATH = FILE_LOC + '\\' + FILE_NAME + '.' + FILE_EXT

    def __init__(self):
        self.check_location = "C:\\Users\\Boo Boo\\Documents\\Ceki"
        self.N1 = "28807288"
        self.N2 = "29373717"
        self.N3 = "999999"
        self.open_settings()

    def print(self):
        print("Settings are:\n"+
              self.check_location + "\n" +
              self.N1 + "\n" +
              self.N2 + "\n" +
              self.N3)

    def open_settings(self):
        Path(self.FILE_LOC).mkdir(parents=True, exist_ok=True)
        file_exists = exists(self.FILE_PATH)
        if (file_exists):
            logger.info("Settings file exists, getting settings")
            with open(self.FILE_PATH, "r",encoding="utf8") as file:
                settings_list = file.readlines()
                for  setting in settings_list:
                    logger.info(setting.strip())
                self.check_location = settings_list[0].strip()
                self.N1 = settings_list[1].strip()
                self.N2 = settings_list[2].strip()
                self.N3 = settings_list[3].strip()
            # subprocess.Popen('explorer "%s"' % self.FILE_LOC)
        else:
            logger.info("Creating settings file")
            self.save_current_settings()

    def save_current_settings(self):
        with open(self.FILE_PATH, "w") as file:
            file = open(self.FILE_PATH, "w", encoding="utf8")
            # File does not exist, creati it with defaults
            file.write(self.check_location + "\n" +
                       self.N1 + "\n" +
                       self.N2 + "\n" +
                       self.N3)