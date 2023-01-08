import logging
import time
import configuration
import threading
import tkinter as tk


root = tk.Tk()
root.withdraw()
REPORT_NO_VALUE = ""


class Buttons:
    __event = None
    BUTTONS = ""
    BUTTONS_LAST = BUTTONS

    def __init__(self, event):
        logging.info('init Buttons')
        self.__event = event
        self.BUTTONS = str(configuration.BUTTON_INDEX) + ":" + "0" * configuration.NR_BUTTONS + ","
        for i in range(0, configuration.NR_BUTTONS):
            button_thread = threading.Thread(name="button_thread_"+str(i), target=self.thread_button, args=(i,))
            button_thread.start()

    def do_slot(self, _):
        # report changes "asynchronously", that is, independently of slot_nr
        ret_val = REPORT_NO_VALUE
        if self.BUTTONS != self.BUTTONS_LAST:
            self.BUTTONS_LAST = self.BUTTONS
            ret_val = self.BUTTONS
        return ret_val

    def thread_button(self, i):
        logging.info("Thread thread_button_" + str(i) + " starting")
        # thread loop
        while self.__event.evt_close_app.is_set() is False:
            if self.__event.evt_set_button_pressed[i].is_set() is True:
                self.BUTTONS = self.BUTTONS[:-2-i] + '1' + self.BUTTONS[-1-i:]
                logging.debug("Button " + str(i) + " set to PRESSED (=HIGH)")
                while (self.__event.evt_set_button_pressed[i].is_set() is True) and \
                        (self.__event.evt_close_app.is_set() is False):
                    time.sleep(configuration.POLL_DELAY_SEC)
            else:
                self.BUTTONS = self.BUTTONS[:-2 - i] + '0' + self.BUTTONS[-1 - i:]
                logging.debug("Button " + str(i) + " set to RELEASED (=LOW)")
                while (self.__event.evt_set_button_pressed[i].is_set() is False) and \
                        (self.__event.evt_close_app.is_set() is False):
                    time.sleep(configuration.POLL_DELAY_SEC)
        logging.info("Thread thread_button_" + str(i) + " finished!")
