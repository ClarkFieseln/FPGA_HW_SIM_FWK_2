import logging
import time
import configuration
import threading
import tkinter as tk


root = tk.Tk()
root.withdraw()
REPORT_NO_VALUE = ""


class Switches:
    __event = None
    # NOTE: due to the slow changes we avoid using a Lock() when accessing SWITCHES
    SWITCHES = ""
    SWITCHES_LAST = SWITCHES

    def __init__(self, event):
        logging.info('init Switches')
        self.__event = event
        self.SWITCHES = str(configuration.SWITCH_INDEX) + ":" + "0" * configuration.NR_SWITCHES + ","
        for i in range(0, configuration.NR_SWITCHES):
            switch_thread = threading.Thread(name="switch_thread_"+str(i), target=self.thread_switch, args=(i,))
            switch_thread.start()

    def do_slot(self, _):
        # report changes "asynchronously", that is, independently of slot_nr
        ret_val = REPORT_NO_VALUE
        if self.SWITCHES != self.SWITCHES_LAST:
            self.SWITCHES_LAST = self.SWITCHES
            ret_val = self.SWITCHES
        return ret_val

    def thread_switch(self, i):
        logging.info("Thread thread_switch_" + str(i) + " starting")
        # thread loop
        while self.__event.evt_close_app.is_set() is False:
            if self.__event.evt_set_switch_right[i].is_set() is True:
                self.SWITCHES = self.SWITCHES[:-2-i] + '1' + self.SWITCHES[-1-i:]
                logging.debug("Switch " + str(i) + " set to RIGHT (=HIGH)")
                while (self.__event.evt_set_switch_right[i].is_set() is True) and \
                        (self.__event.evt_close_app.is_set() is False):
                    time.sleep(configuration.POLL_DELAY_SEC)
            else:
                self.SWITCHES = self.SWITCHES[:-2 - i] + '0' + self.SWITCHES[-1 - i:]
                logging.debug("Switch " + str(i) + " set to LEFT (=LOW)")
                while (self.__event.evt_set_switch_right[i].is_set() is False) and \
                        (self.__event.evt_close_app.is_set() is False):
                    time.sleep(configuration.POLL_DELAY_SEC)
        logging.info("Thread thread_switch_" + str(i) + " finished!")
