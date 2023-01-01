import random
import configuration
import logging
import tkinter
import threading
import time


# simulation options:
#####################
# simulate DI changes in separate threads, independent of scheduler?
DO_CHANGES_IN_THREADS = True
# simulate random numbers or counter?
DO_RND_DIS = False


root = tkinter.Tk()
root.withdraw()
SYNC_DI_IDX = []
ASYNC_DI_IDX = []
DI_SYNC_CLK_PERIODS = 10
DI_ASYNC_CLK_PERIODS = 10
DI_SYNC_PERIOD_SEC = 0.1
DI_ASYNC_PERIOD_SEC = 0.1
REPORT_NO_VALUE = ""
FMT_SYNC = "{0:0" + str(configuration.NR_SYNC_DIS) + "b}"
FMT_ASYNC = "{0:0" + str(configuration.NR_ASYNC_DIS) + "b}"
SLOT_CLOCK_RAISING_EDGE = configuration.SLOT_CLOCK_RAISING_EDGE
SLOT_CLOCK_HIGH_LEVEL = configuration.SLOT_CLOCK_HIGH_LEVEL
SLOT_CLOCK_FALLING_EDGE = configuration.SLOT_CLOCK_FALLING_EDGE
SLOT_CLOCK_LOW_LEVEL = configuration.SLOT_CLOCK_LOW_LEVEL


class DigitalInputs:
    __event = None
    CLOCK_PERIOD_SEC = None
    DIS = str(configuration.DI_INDEX) + ":" + "0" * configuration.NR_ASYNC_DIS + "0" * configuration.NR_SYNC_DIS + ","
    DIS_LAST = DIS
    __di_sync_count = 0
    __di_async_count = 0
    cnt_sync_clock_periods = 0
    cnt_async_clock_periods = 0

    def __init__(self, event, clock_period_sec):
        logging.info('init DigitalInputs')
        self.__event = event
        self.CLOCK_PERIOD_SEC = clock_period_sec
        for i in range(configuration.NR_SYNC_DIS):
            SYNC_DI_IDX.append(i)
        if DO_CHANGES_IN_THREADS is True:
            di_sync_thread = threading.Thread(name="di_sync_thread", target=self.di_sync_thread)
            di_sync_thread.start()
        for i in range(configuration.NR_ASYNC_DIS):
            # by convention all async DIs are stored at the end of the list
            ASYNC_DI_IDX.append(configuration.NR_ASYNC_DIS + i)
        if DO_CHANGES_IN_THREADS is True:
            di_async_thread = threading.Thread(name="di_async_thread", target=self.di_async_thread)
            di_async_thread.start()

    def update_di_sync(self):
        # update DIS with __di_sync_count
        self.DIS = self.DIS[0: len(str(configuration.DI_INDEX)) + 1 + configuration.NR_ASYNC_DIS] + \
                   FMT_SYNC.format(self.__di_sync_count) + self.DIS[-1]
        logging.debug(self.DIS)
        # inform GUI
        self.__event.evt_gui_di_update.set()
        if DO_RND_DIS is True:
            # assign a random number to sync counter
            self.__di_sync_count = random.randint(0, 2 ** configuration.NR_SYNC_DIS)
        else:
            # increment sync counter
            self.__di_sync_count = (self.__di_sync_count + 1) % (2 ** configuration.NR_SYNC_DIS)

    def update_di_async(self):
        # update DIS with __di_async_count
        self.DIS = self.DIS[0: len(str(configuration.DI_INDEX)) + 1] + \
                   FMT_ASYNC.format(self.__di_async_count) + self.DIS[-(configuration.NR_ASYNC_DIS + 1):]
        logging.debug(self.DIS)
        # inform GUI
        self.__event.evt_gui_di_update.set()
        if DO_RND_DIS is True:
            # assign a random number to async counter
            self.__di_async_count = random.randint(0, 2 ** configuration.NR_ASYNC_DIS)
        else:
            # increment async counter
            self.__di_async_count = (self.__di_async_count + 1) % (2 ** configuration.NR_ASYNC_DIS)

    # update sync DIs independently of scheduler
    def di_sync_thread(self):
        logging.info("Thread di_sync_thread starting")
        # thread loop
        while self.__event.evt_close_app.is_set() is False:
            self.update_di_sync()
            # wait for DI_ASYNC_PERIOD_SEC
            if self.CLOCK_PERIOD_SEC[0] > 0:
                while self.__event.evt_close_app.is_set() is False:
                    time.sleep(self.CLOCK_PERIOD_SEC[0] * DI_SYNC_CLK_PERIODS)
            else:
                time.sleep(DI_SYNC_PERIOD_SEC)
        logging.info("Thread di_sync_thread finished!")

    # update async DIs independently of scheduler
    def di_async_thread(self):
        logging.info("Thread di_async_thread starting")
        # thread loop
        while self.__event.evt_close_app.is_set() is False:
            self.update_di_async()
            # wait for DI_ASYNC_PERIOD_SEC
            if self.CLOCK_PERIOD_SEC[0] > 0:
                while self.__event.evt_close_app.is_set() is False:
                    time.sleep(self.CLOCK_PERIOD_SEC[0] * DI_ASYNC_CLK_PERIODS)
            else:
                time.sleep(DI_ASYNC_PERIOD_SEC)
        logging.info("Thread di_async_thread finished!")

    # called from GUI
    def get_dis(self, i):
        return self.DIS[-2 - i]

    # called from scheduler
    def do_slot(self, slot_nr):
        ret_val = REPORT_NO_VALUE
        check_changes = False
        if DO_CHANGES_IN_THREADS is False:
            # clk stable value = high? -> update async DIs
            # these values will be "seen" in VHDL on the next clock falling edge
            if slot_nr == SLOT_CLOCK_HIGH_LEVEL:
                self.cnt_async_clock_periods = (self.cnt_async_clock_periods + 1) % DI_ASYNC_CLK_PERIODS
                if self.cnt_async_clock_periods == 0:
                    self.update_di_async()
                    check_changes = True
            # clk raising edge? -> update sync DIs
            if slot_nr == SLOT_CLOCK_RAISING_EDGE:
                self.cnt_sync_clock_periods = (self.cnt_sync_clock_periods + 1) % DI_SYNC_CLK_PERIODS
                if self.cnt_sync_clock_periods == 0:
                    self.update_di_sync()
                    check_changes = True
        else:
            check_changes = True
        if check_changes is True:
            if (slot_nr == SLOT_CLOCK_RAISING_EDGE) or (slot_nr == SLOT_CLOCK_HIGH_LEVEL):
                if self.DIS != self.DIS_LAST:
                    self.DIS_LAST = self.DIS
                    ret_val = self.DIS
        return ret_val
