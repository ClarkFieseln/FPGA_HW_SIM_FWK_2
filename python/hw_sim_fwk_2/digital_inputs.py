import random
import configuration
import logging
import tkinter as tk
from tkinter import filedialog, messagebox
import threading
import time
from websocket_server import WebSocketServer
import pathlib
import os


root = tk.Tk()
root.withdraw()
SYNC_DI_IDX = []
ASYNC_DI_IDX = []
DI_SYNC_CLK_PERIODS = 10
DI_ASYNC_CLK_PERIODS = 10
DI_SYNC_PERIOD_SEC = 0.1
DI_ASYNC_PERIOD_SEC = 0.1
REPORT_NO_VALUE = ""
SLOT_CLOCK_RAISING_EDGE = configuration.SLOT_CLOCK_RAISING_EDGE
SLOT_CLOCK_HIGH_LEVEL = configuration.SLOT_CLOCK_HIGH_LEVEL
SLOT_CLOCK_FALLING_EDGE = configuration.SLOT_CLOCK_FALLING_EDGE
SLOT_CLOCK_LOW_LEVEL = configuration.SLOT_CLOCK_LOW_LEVEL


class DigitalInputs:
    dis_filename = "dis.txt"
    __event = None
    CLOCK_PERIOD_SEC = None
    DIS = ""
    DIS_LAST = DIS
    __di_sync_count = 0
    __di_async_count = 0
    cnt_sync_clock_periods = 0
    cnt_async_clock_periods = 0
    FMT_SYNC = ""
    FMT_ASYNC = ""
    dis_from_file = []
    idx = 0
    idx_max = 0
    update_di_sync = None
    update_di_async = None    

    def __init__(self, event, clock_period_sec):
        logging.info('init DigitalInputs')
        self.__event = event
        self.CLOCK_PERIOD_SEC = clock_period_sec
        self.FMT_SYNC = "{0:0" + str(configuration.NR_SYNC_DIS) + "b}"
        self.FMT_ASYNC = "{0:0" + str(configuration.NR_ASYNC_DIS) + "b}"
        self.DIS = str(configuration.DI_INDEX) + ":" + "0" * configuration.NR_ASYNC_DIS + \
                   "0" * configuration.NR_SYNC_DIS + ","              
        if configuration.DO_DIS == configuration.DO_CIRCUITJS_DIS:
            self.update_di_sync = self.update_di_sync_circuitjs
            self.update_di_async = self.update_di_async_circuitjs
            # start WebSocketServer in a separate thread
            thread = threading.Thread(target=self.start_websocket_server,
                                      args=(self.__event, self.update_di_sync, self.update_di_async))
            thread.start()
        elif configuration.DO_DIS == configuration.DO_FILE_DIS:
            self.update_di_sync = self.update_di_sync_file
            self.update_di_async = self.update_di_async_file
            # script or .exe?
            runningScript = os.path.basename(__file__)
            # we get different relative paths if we debug or run the executable file
            if runningScript == "digital_inputs.py":
                # .py script
                PATH_PREFIX = str(pathlib.Path().resolve()) + "/dist/"
            else:
                # .exe file
                PATH_PREFIX = str(pathlib.Path().resolve()) + "/"
            self.dis_filename = PATH_PREFIX + self.dis_filename
            if pathlib.Path(self.dis_filename).is_file():
                file_name = self.dis_filename
            else:
                tk.messagebox.showinfo(title="INFO", message="Please select a file for simulation of DIs")
                files = [('All Files', '*.*'),
                         ('Input Files', '*.in'),
                         ('Text Document', '*.txt')]
                file_name = filedialog.askopenfilename(initialdir=PATH_PREFIX, filetypes=files, defaultextension="txt")
            if file_name != '':
                file_in = open(file_name, 'r')
                for y in file_in.read().split('\n'):
                    try:
                        if (int(y) < (2 ** configuration.NR_SYNC_DIS)) and (int(y) < (2 ** configuration.NR_ASYNC_DIS)):
                            self.dis_from_file.append(int(y))
                        else:
                            self.dis_from_file.append(0)
                        self.idx_max = self.idx_max + 1
                    except Exception as _:
                        pass
            else:
                self.dis_from_file.append(0)
                self.idx_max = 1
                tk.messagebox.showwarning(title="WARNING",
                                          message="No input file selected for simulation of digital inputs!")
        elif configuration.DO_DIS == configuration.DO_RND_DIS:
            self.update_di_sync = self.update_di_sync_rnd
            self.update_di_async = self.update_di_async_rnd
        elif configuration.DO_DIS == configuration.DO_CNT_DIS:
            self.update_di_sync = self.update_di_sync_cnt
            self.update_di_async = self.update_di_async_cnt
        # WORKAROUND: in case sync or async DIs is zero
        if configuration.NR_SYNC_DIS <= 0:
            self.update_di_sync = self.update_di_sync_dummy
        if configuration.NR_ASYNC_DIS <= 0:
            self.update_di_async = self.update_di_async_dummy
        # threads
        for i in range(configuration.NR_SYNC_DIS):
            SYNC_DI_IDX.append(i)
        if (configuration.DO_DI_CHANGES_IN_THREAD is True) and (configuration.DO_DIS != configuration.DO_CIRCUITJS_DIS):
            if configuration.NR_SYNC_DIS > 0:
                di_sync_thread = threading.Thread(name="di_sync_thread", target=self.di_sync_thread)
                di_sync_thread.start()
        for i in range(configuration.NR_ASYNC_DIS):
            # by convention all async DIs are stored at the end of the list
            ASYNC_DI_IDX.append(configuration.NR_ASYNC_DIS + i)
        if (configuration.DO_DI_CHANGES_IN_THREAD is True) and (configuration.DO_DIS != configuration.DO_CIRCUITJS_DIS):
            if configuration.NR_ASYNC_DIS > 0:
                di_async_thread = threading.Thread(name="di_async_thread", target=self.di_async_thread)
                di_async_thread.start()

    @staticmethod
    def start_websocket_server(event, update_di_sync, update_di_async):
        logging.info("start_websocket_server started")
        # "blocking" call until the client is connected,
        # then continue to block inside a 2nd event loop
        WebSocketServer.websocket_thread(event, update_di_sync, update_di_async)
        logging.info("start_websocket_server finished!")

    def update_dis_sync(self):
        # update DIS with __di_sync_count
        self.DIS = self.DIS[0: len(str(configuration.DI_INDEX)) + 1 + configuration.NR_ASYNC_DIS] + \
                   self.FMT_SYNC.format(self.__di_sync_count) + self.DIS[-1]
        # inform GUI
        # self.__event.evt_gui_di_update.set()  # NOTE: update instead in do_slot() when self.DIS != self.DIS_LAST
        
    def update_di_sync_dummy(self):
        return
    
    def update_di_sync_rnd(self):
        # assign a random number to sync
        self.__di_sync_count = random.randint(0, 2 ** configuration.NR_SYNC_DIS)
        self.update_dis_sync()

    def update_di_sync_cnt(self):
        # increment sync
        self.__di_sync_count = (self.__di_sync_count + 1) % (2 ** configuration.NR_SYNC_DIS)
        self.update_dis_sync()

    def update_di_sync_file(self):
        self.__di_sync_count = self.dis_from_file[self.idx]
        # NOTE index is incremented only in sync call in order to use the same data in async
        self.idx = (self.idx + 1) % self.idx_max
        self.update_dis_sync()

    def update_di_sync_circuitjs(self):
        # set sync with value obtained from circuitjs
        self.__di_sync_count = int(WebSocketServer.get_normalized_input_data() * (2 ** configuration.NR_SYNC_DIS))
        self.update_dis_sync()

    def update_dis_async(self):
        # update DIS with __di_async_count
        self.DIS = self.DIS[0: len(str(configuration.DI_INDEX)) + 1] + \
                   self.FMT_ASYNC.format(self.__di_async_count) + self.DIS[-(configuration.NR_SYNC_DIS + 1):]
        # inform GUI
        # self.__event.evt_gui_di_update.set()  # NOTE: update instead in do_slot() when self.DIS != self.DIS_LAST
        
    def update_di_async_dummy(self):
        return
    
    def update_di_async_rnd(self):
        # assign a random number to async
        self.__di_async_count = random.randint(0, 2 ** configuration.NR_ASYNC_DIS)
        self.update_dis_async()

    def update_di_async_cnt(self):
        # increment async
        self.__di_async_count = (self.__di_async_count + 1) % (2 ** configuration.NR_ASYNC_DIS)
        self.update_dis_async()

    def update_di_async_file(self):
        # NOTE: we use the same data as in sync
        self.__di_async_count = self.dis_from_file[self.idx]
        self.update_dis_async()

    def update_di_async_circuitjs(self):
        # set async with value obtained from circuitjs
        self.__di_async_count = int(WebSocketServer.get_normalized_input_data() * (2 ** configuration.NR_ASYNC_DIS))
        self.update_dis_async()

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
        if configuration.DO_DI_CHANGES_IN_THREAD is False:
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
            # NOTE: check every time if there are changes...that is, we are fully async!
            #       alternatively, we could react only to clock raising edge (sync) and clock high (async) with:
            #       if (slot_nr == SLOT_CLOCK_RAISING_EDGE) or (slot_nr == SLOT_CLOCK_HIGH_LEVEL):
            if self.DIS != self.DIS_LAST:
                self.DIS_LAST = self.DIS
                ret_val = self.DIS
                # inform GUI
                self.__event.evt_gui_di_update.set()
        return ret_val





