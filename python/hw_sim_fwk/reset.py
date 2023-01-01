import logging
import time
import configuration
import threading
import tkinter as tk


root = tk.Tk()
root.withdraw()
REPORT_NO_VALUE = ""
REPORT_RESET_HIGH = configuration.RESET_INDEX + ":1,"
REPORT_RESET_LOW = configuration.RESET_INDEX + ":0,"


class Reset:
    __event = None
    # NOTE: due to the slow changes we avoid using a Lock() when accessing the report variable
    report = REPORT_NO_VALUE

    def __init__(self, event):
        logging.info('init Reset')
        self.__event = event
        reset_thread = threading.Thread(name="reset_thread", target=self.thread_reset)
        reset_thread.start()

    def do_slot(self, _):
        # report changes "asynchronously", that is, independently of slot_nr
        ret_val = REPORT_NO_VALUE
        if self.report != REPORT_NO_VALUE:
            ret_val = self.report
            self.report = REPORT_NO_VALUE
        return ret_val

    def thread_reset(self):
        logging.info("Thread thread_reset starting")
        # thread loop
        while self.__event.evt_close_app.is_set() is False:
            if self.__event.evt_set_reset_high.is_set() is False:
                self.report = REPORT_RESET_LOW
                logging.debug("Reset set to LOW")
                while (self.__event.evt_set_reset_high.is_set() is False) and \
                        (self.__event.evt_close_app.is_set() is False):
                    time.sleep(configuration.POLL_DELAY_SEC)
            else:
                self.report = REPORT_RESET_HIGH
                logging.debug("Reset set to HIGH")
                while (self.__event.evt_set_reset_high.is_set() is True) and \
                        (self.__event.evt_close_app.is_set() is False):
                    time.sleep(configuration.POLL_DELAY_SEC)
        logging.info("Thread thread_reset finished!")
