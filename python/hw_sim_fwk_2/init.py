import configuration
import configparser
import os
import tkinter as tk
from tkinter import filedialog, messagebox
import pathlib
import logging


# we need this, otherwise we see the Tk window
root = tk.Tk()
root.withdraw()


class InitApp(object):
    config = configparser.ConfigParser(allow_no_value=True)
    config_filename = "config.ini"
    
    def __init__(self):
        # script or .exe?
        runningScript = os.path.basename(__file__)
        # we get different relative paths if we debug or run the executable file
        if runningScript == "init.py":
            # .py script
            PATH_PREFIX = str(pathlib.Path().resolve()) + "\\dist\\"
        else:
            # .exe file
            PATH_PREFIX = str(pathlib.Path().resolve()) + "\\"
        self.config_filename = PATH_PREFIX + self.config_filename
        # file exists?
        if pathlib.Path(self.config_filename).is_file():
            # Load the configuration file
            self.load_config_file(self.config_filename)
        else:
            tk.messagebox.showinfo(title="INFO", message="Please select a configuration file if available.")
            files = [('Ini Files', '*.ini'),
                     ('Configuration Files', '*.cfg'),
                     ('Text Document', '*.txt'),
                     ('All Files', '*.*')]
            self.config_filename = \
                filedialog.askopenfilename(initialdir=PATH_PREFIX, filetypes=files, defaultextension="ini")
            if self.config_filename != '':
                # Load the configuration file
                self.load_config_file(self.config_filename)
            else:
                tk.messagebox.showwarning(title="WARNING",
                                          message="No config.ini file found. Default settings will be used!")

    # NOTE: LOGGING_LEVEL is read in main.py
    def load_config_file(self, filename):
        logging.info("reading " + filename)
        try:
            self.config.read(filename)
            logging.info("sections: " + str(self.config.sections()))
            if "myConfig" in self.config:
                logging.info("keys in section myConfig:")
                if "LOGGING_LEVEL" in self.config["myConfig"]:
                    configuration.LOGGING_LEVEL = self.config['myConfig']['LOGGING_LEVEL']
                    logging.info("LOGGING_LEVEL = " + str(configuration.LOGGING_LEVEL))
                if "GUI_UPDATE_PERIOD_IN_HZ" in self.config["myConfig"]:
                    configuration.GUI_UPDATE_RATE_IN_HZ = int(self.config['myConfig']['GUI_UPDATE_RATE_IN_HZ'])
                    logging.info("GUI_UPDATE_RATE_IN_HZ = " + str(configuration.GUI_UPDATE_RATE_IN_HZ))
                if "ESTIMATED_CLOCK_SIMULATION_RATE" in self.config["myConfig"]:
                    configuration.ESTIMATED_CLOCK_SIMULATION_RATE = \
                        int(self.config['myConfig']['ESTIMATED_CLOCK_SIMULATION_RATE'])
                    logging.info("ESTIMATED_CLOCK_SIMULATION_RATE = " +
                                 str(configuration.ESTIMATED_CLOCK_SIMULATION_RATE))
                if "POLL_DELAY_SEC" in self.config["myConfig"]:
                    configuration.POLL_DELAY_SEC = self.config.getfloat('myConfig', 'POLL_DELAY_SEC')
                    logging.info("POLL_DELAY_SEC = " + str(configuration.POLL_DELAY_SEC))
                if "NR_BUTTONS" in self.config["myConfig"]:
                    configuration.NR_BUTTONS = self.config.getint('myConfig', 'NR_BUTTONS')
                    logging.info("NR_BUTTONS = " + str(configuration.NR_BUTTONS))
                if "NR_SWITCHES" in self.config["myConfig"]:
                    configuration.NR_SWITCHES = self.config.getint('myConfig', 'NR_SWITCHES')
                    logging.info("NR_SWITCHES = " + str(configuration.NR_SWITCHES))
                if "NR_DIS" in self.config["myConfig"]:
                    configuration.NR_DIS = self.config.getint('myConfig', 'NR_DIS')
                    logging.info("NR_DIS = " + str(configuration.NR_DIS))
                if "NR_DOS" in self.config["myConfig"]:
                    configuration.NR_DOS = self.config.getint('myConfig', 'NR_DOS')
                    logging.info("NR_DOS = " + str(configuration.NR_DOS))
                if "NR_LEDS" in self.config["myConfig"]:
                    configuration.NR_LEDS = self.config.getint('myConfig', 'NR_LEDS')
                    logging.info("NR_LEDS = " + str(configuration.NR_LEDS))
                if "NR_ASYNC_DIS" in self.config["myConfig"]:
                    configuration.NR_ASYNC_DIS = self.config.getint('myConfig', 'NR_ASYNC_DIS')
                    logging.info("NR_ASYNC_DIS = " + str(configuration.NR_ASYNC_DIS))
                if "NR_SYNC_DIS" in self.config["myConfig"]:
                    configuration.NR_SYNC_DIS = self.config.getint('myConfig', 'NR_SYNC_DIS')
                    logging.info("NR_SYNC_DIS = " + str(configuration.NR_SYNC_DIS))
                if "CLOCK_INDEX" in self.config["myConfig"]:
                    configuration.CLOCK_INDEX = self.config['myConfig']['CLOCK_INDEX']
                    logging.info("CLOCK_INDEX = " + configuration.CLOCK_INDEX)
                if "RESET_INDEX" in self.config["myConfig"]:
                    configuration.RESET_INDEX = self.config['myConfig']['RESET_INDEX']
                    logging.info("RESET_INDEX = " + configuration.RESET_INDEX)
                if "BUTTON_INDEX" in self.config["myConfig"]:
                    configuration.BUTTON_INDEX = self.config['myConfig']['BUTTON_INDEX']
                    logging.info("BUTTON_INDEX = " + configuration.BUTTON_INDEX)
                if "SWITCH_INDEX" in self.config["myConfig"]:
                    configuration.SWITCH_INDEX = self.config['myConfig']['SWITCH_INDEX']
                    logging.info("SWITCH_INDEX = " + configuration.SWITCH_INDEX)
                if "DI_INDEX" in self.config["myConfig"]:
                    configuration.DI_INDEX = self.config['myConfig']['DI_INDEX']
                    logging.info("DI_INDEX = " + configuration.DI_INDEX)
                if "DO_INDEX" in self.config["myConfig"]:
                    configuration.DO_INDEX = self.config['myConfig']['DO_INDEX']
                    logging.info("DO_INDEX = " + configuration.DO_INDEX)
                if "LED_INDEX" in self.config["myConfig"]:
                    configuration.LED_INDEX = self.config['myConfig']['LED_INDEX']
                    logging.info("LED_INDEX = " + configuration.LED_INDEX)
                if "FIFO_WRITE_BUFFER_SIZE" in self.config["myConfig"]:
                    configuration.FIFO_WRITE_BUFFER_SIZE = self.config.getint('myConfig', 'FIFO_WRITE_BUFFER_SIZE')
                    logging.info("FIFO_WRITE_BUFFER_SIZE = " + str(configuration.FIFO_WRITE_BUFFER_SIZE))
                if "FIFO_READ_BUFFER_SIZE" in self.config["myConfig"]:
                    configuration.FIFO_READ_BUFFER_SIZE = self.config.getint('myConfig', 'FIFO_READ_BUFFER_SIZE')
                    logging.info("FIFO_READ_BUFFER_SIZE = " + str(configuration.FIFO_READ_BUFFER_SIZE))
                if "DO_DI_CHANGES_IN_THREAD" in self.config["myConfig"]:
                    configuration.DO_DI_CHANGES_IN_THREAD = \
                        self.config.getboolean('myConfig', 'DO_DI_CHANGES_IN_THREAD')
                    logging.info("DO_DI_CHANGES_IN_THREAD = " + str(configuration.DO_DI_CHANGES_IN_THREAD))
                if "DO_CIRCUITJS_DIS" in self.config["myConfig"]:
                    configuration.DO_CIRCUITJS_DIS = self.config.getint('myConfig', 'DO_CIRCUITJS_DIS')
                    logging.info("DO_CIRCUITJS_DIS = " + str(configuration.DO_CIRCUITJS_DIS))
                if "DO_FILE_DIS" in self.config["myConfig"]:
                    configuration.DO_FILE_DIS = self.config.getint('myConfig', 'DO_FILE_DIS')
                    logging.info("DO_FILE_DIS = " + str(configuration.DO_FILE_DIS))
                if "DO_RND_DIS" in self.config["myConfig"]:
                    configuration.DO_RND_DIS = self.config.getint('myConfig', 'DO_RND_DIS')
                    logging.info("DO_RND_DIS = " + str(configuration.DO_RND_DIS))
                if "DO_CNT_DIS" in self.config["myConfig"]:
                    configuration.DO_CNT_DIS = self.config.getint('myConfig', 'DO_CNT_DIS')
                    logging.info("DO_CNT_DIS = " + str(configuration.DO_CNT_DIS))
                if "DO_DIS" in self.config["myConfig"]:
                    configuration.DO_DIS = self.config.getint('myConfig', 'DO_DIS')
                    logging.info("DO_DIS = " + str(configuration.DO_DIS))
                if "FIFO_PATH" in self.config["myConfig"]:
                    configuration.FIFO_PATH = self.config['myConfig']['FIFO_PATH']
                    logging.info("FIFO_PATH = " + configuration.FIFO_PATH)
                if "RUN_FOR_CLOCK_PERIODS" in self.config["myConfig"]:
                    configuration.RUN_FOR_CLOCK_PERIODS = self.config.getint('myConfig', 'RUN_FOR_CLOCK_PERIODS')
                    logging.info("RUN_FOR_CLOCK_PERIODS = " + str(configuration.RUN_FOR_CLOCK_PERIODS))
                if "RESET_FOR_CLOCK_PERIODS" in self.config["myConfig"]:
                    configuration.RESET_FOR_CLOCK_PERIODS = self.config.getint('myConfig', 'RESET_FOR_CLOCK_PERIODS')
                    logging.info("RESET_FOR_CLOCK_PERIODS = " + str(configuration.RESET_FOR_CLOCK_PERIODS))
                if "CLOCK_PERIOD_EXTERNAL" in self.config["myConfig"]:
                    configuration.CLOCK_PERIOD_EXTERNAL = self.config['myConfig']['CLOCK_PERIOD_EXTERNAL']
                    logging.info("CLOCK_PERIOD_EXTERNAL = " + configuration.CLOCK_PERIOD_EXTERNAL)
                if "CLOCK_PERIOD_EXTERNAL_MIN_MS" in self.config["myConfig"]:
                    configuration.CLOCK_PERIOD_EXTERNAL_MIN_MS = \
                        self.config.getfloat('myConfig', 'CLOCK_PERIOD_EXTERNAL_MIN_MS')
                    logging.info("CLOCK_PERIOD_EXTERNAL_MIN_MS = " + str(configuration.CLOCK_PERIOD_EXTERNAL_MIN_MS))
            else:
                logging.error("Could not load config file: " + filename)
        except (configparser.NoSectionError, configparser.MissingSectionHeaderError):
            logging.error("Exception raised in init.load_config_file() trying to load config file!\n")
            pass
