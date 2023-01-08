import time
import configuration
import logging
import threading
import traceback
import tkinter as tk
from tkinter import messagebox
from inspect import currentframe


root = tk.Tk()
root.withdraw()
cf = currentframe()


class Clock:
    CLOCK_PERIOD_SEC = None
    default_estimated_clock_simulation_rate = 0
    __event = None

    def __init__(self, event, clock_period_sec):
        logging.info('init clock')
        self.__event = event
        self.CLOCK_PERIOD_SEC = clock_period_sec
        self.update_gui_defs()
        thread_clock = threading.Thread(name="clock_thread", target=self.thread_clock)
        thread_clock.start()

    def update_gui_defs(self):
        # check ranges
        if configuration.CLOCK_PERIOD_EXTERNAL_MIN_MS <= 0.0:
            # NOTE: 100 ms hardcoded rescue value.
            configuration.CLOCK_PERIOD_EXTERNAL_MIN_MS = 100.0
            logging.error("min. clock period shall be greater than zero. Now set to value = 100 ms")
            tk.messagebox.showerror(title="ERROR",
                                    message="min. clock period shall be greater than zero. Now set to value = 100 ms")
            root.update()
        if float(configuration.CLOCK_PERIOD_EXTERNAL.partition(" ")[0]) < 0.0:
            configuration.CLOCK_PERIOD_EXTERNAL = str(configuration.CLOCK_PERIOD_EXTERNAL_MIN_MS) + " ms"
            logging.error("clock period shall be greater than zero. Now set to minimum value = " + str(
                configuration.CLOCK_PERIOD_EXTERNAL_MIN_MS) + " ms")
            tk.messagebox.showerror(title="ERROR",
                                    message="clock period shall be greater than zero. Now set to minimum value = "
                                            + str(configuration.CLOCK_PERIOD_EXTERNAL_MIN_MS) + " ms")
            root.update()
        # NOTE: self.CLOCK_PERIOD_SEC[0] corresponds exactly to one period in VHDL code.
        if " fs" in configuration.CLOCK_PERIOD_EXTERNAL:
            self.CLOCK_PERIOD_SEC[0] = float(configuration.CLOCK_PERIOD_EXTERNAL.partition(" ")[0]) / 1000000000000000.0
        elif " ps" in configuration.CLOCK_PERIOD_EXTERNAL:
            self.CLOCK_PERIOD_SEC[0] = float(configuration.CLOCK_PERIOD_EXTERNAL.partition(" ")[0]) / 1000000000000.0
        elif " ns" in configuration.CLOCK_PERIOD_EXTERNAL:
            self.CLOCK_PERIOD_SEC[0] = float(configuration.CLOCK_PERIOD_EXTERNAL.partition(" ")[0]) / 1000000000.0
        elif " us" in configuration.CLOCK_PERIOD_EXTERNAL:
            self.CLOCK_PERIOD_SEC[0] = float(configuration.CLOCK_PERIOD_EXTERNAL.partition(" ")[0]) / 1000000.0
        elif " ms" in configuration.CLOCK_PERIOD_EXTERNAL:
            self.CLOCK_PERIOD_SEC[0] = float(configuration.CLOCK_PERIOD_EXTERNAL.partition(" ")[0]) / 1000.0
        elif " sec" in configuration.CLOCK_PERIOD_EXTERNAL:
            self.CLOCK_PERIOD_SEC[0] = float(configuration.CLOCK_PERIOD_EXTERNAL.partition(" ")[0])
        elif " min" in configuration.CLOCK_PERIOD_EXTERNAL:
            self.CLOCK_PERIOD_SEC[0] = float(configuration.CLOCK_PERIOD_EXTERNAL.partition(" ")[0]) * 60.0
        elif " min" in configuration.CLOCK_PERIOD_EXTERNAL:
            self.CLOCK_PERIOD_SEC[0] = float(configuration.CLOCK_PERIOD_EXTERNAL.partition(" ")[0]) * 3600.0
        else:
            logging.error("Error: unknown time units in CLOCK_PERIOD_EXTERNAL!")
            traceback.print_exc()
            exit(cf.f_lineno)
        logging.info("CLOCK_PERIOD_SEC = " + str(self.CLOCK_PERIOD_SEC[0]))
        # adapt ESTIMATED_CLOCK_RATE
        # in order to update the actual rate on the GUI every "1 second"
        if self.CLOCK_PERIOD_SEC[0] != 0:
            configuration.ESTIMATED_CLOCK_SIMULATION_RATE = int(1 / self.CLOCK_PERIOD_SEC[0])
        else:
            self.default_estimated_clock_simulation_rate = configuration.ESTIMATED_CLOCK_SIMULATION_RATE

    def set_clock_period_ms(self, clock_period_ms):
        if clock_period_ms != 0:
            if clock_period_ms >= configuration.CLOCK_PERIOD_EXTERNAL_MIN_MS:
                temp = clock_period_ms / 1000.0
            else:
                temp = configuration.CLOCK_PERIOD_EXTERNAL_MIN_MS / 1000.0
        else:
            temp = 0.0
        # first adapt ESTIMATED_CLOCK_RATE (otherwise we may never reach big values in scheduler when changing)
        # in order to update the actual rate on the GUI every "1 second"
        if temp != 0.0:
            configuration.ESTIMATED_CLOCK_SIMULATION_RATE = int(1 / temp)
        else:
            configuration.ESTIMATED_CLOCK_SIMULATION_RATE = self.default_estimated_clock_simulation_rate
        self.CLOCK_PERIOD_SEC[0] = temp

    def thread_clock(self):
        logging.info("Thread thread_clock starting")
        while self.__event.evt_close_app.is_set() is False:
            # need clock or run in TURBO mode?
            if self.CLOCK_PERIOD_SEC[0] > 0:
                # raise event for new clock transition
                self.__event.evt_clock.set()
                # wait half clock period
                time.sleep(self.CLOCK_PERIOD_SEC[0] / configuration.TIME_SLOTS)
            else:
                # wait to check every once in a while for a change in CLOCK_PERIOD_SEC
                time.sleep(configuration.POLL_DELAY_SEC)
        # set event to indicate that the clock has finished
        self.__event.evt_clock_finished.set()
        logging.info("Thread thread_clock finished!")
