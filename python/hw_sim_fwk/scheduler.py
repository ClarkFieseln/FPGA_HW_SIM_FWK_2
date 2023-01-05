import logging
import configuration
from inspect import currentframe
import win32file
import win32pipe
import threading
import tkinter
import time
from common_fifo import create_w_fifo, create_r_fifo


# from https://discuss.python.org/t/higher-resolution-timers-on-windows/16153
#############################################################################
import ctypes
ntdll = ctypes.WinDLL('NTDLL.DLL')
NSEC_PER_SEC = 1000000000


def set_resolution_ns(resolution):
    # NtSetTimerResolution uses 100ns units
    resolution = ctypes.c_ulong(int(resolution // 100))
    current = ctypes.c_ulong()
    status_success = 0
    r = ntdll.NtSetTimerResolution(resolution, 1, ctypes.byref(current))
    if r != status_success:
        logging.error("The call to ntdll.NtSetTimerResolution() has failed!")
    # NtSetTimerResolution uses 100ns units
    return current.value * 100


set_resolution_ns(1e-9 * NSEC_PER_SEC)
#############################################################################


root = tkinter.Tk()
root.withdraw()
cf = currentframe()

###############################################################
#
#        |<---1 period-->|
#         ___1____        ___1_...
#        |       |       |
#        0       2       0
#  ...___|       |___3___|
#
TIME_SLOTS = configuration.TIME_SLOTS
SLOT_CLOCK_RAISING_EDGE = configuration.SLOT_CLOCK_RAISING_EDGE
SLOT_CLOCK_HIGH_LEVEL = configuration.SLOT_CLOCK_HIGH_LEVEL
SLOT_CLOCK_FALLING_EDGE = configuration.SLOT_CLOCK_FALLING_EDGE
SLOT_CLOCK_LOW_LEVEL = configuration.SLOT_CLOCK_LOW_LEVEL
###############################################################

FILE_NAME_FIFO_APP_TO_SIM = configuration.FIFO_PATH + "fifo_app_to_sim"
FILE_NAME_FIFO_SIM_TO_APP = configuration.FIFO_PATH + "fifo_sim_to_app"
REPORT_CLOCK_HIGH = configuration.CLOCK_INDEX + ":1,"
REPORT_CLOCK_LOW = configuration.CLOCK_INDEX + ":0,"
LED_HEADER = configuration.LED_INDEX + ":"
DO_HEADER = configuration.DO_INDEX + ":"
FIFO_READ_BUFFER_SIZE = configuration.FIFO_READ_BUFFER_SIZE


class Scheduler:
    restart: bool = False
    CLOCK_PERIOD_SEC = None
    start_time_abs = 0
    nr_cycles = 0
    clock_periods = 0
    simulation_frequency = 0
    remaining_clock_periods_to_run = 0  # TODO: add getter/setter
    __event = None
    time_slot = 0
    stepping = False
    digital_inputs = None
    digital_outputs = None
    leds = None
    reset = None
    switches = None
    buttons = None
    fifo_app_to_sim = None
    fifo_sim_to_app = None

    def __init__(self, event, clock_period_sec, ref):
        logging.info('init Scheduler')
        self.__event = event
        self.CLOCK_PERIOD_SEC = clock_period_sec
        self.reset = ref.reset
        self.leds = ref.leds
        self.switches = ref.switches
        self.digital_inputs = ref.digital_inputs
        self.digital_outputs = ref.digital_outputs
        self.buttons = ref.buttons
        scheduler_thread = threading.Thread(name="scheduler_thread", target=self.thread_scheduler)
        scheduler_thread.start()

    def restart_counters(self):
        self.restart = True

    def do_slot(self, slot_nr, input_fifo):
        logging.debug("slot_nr = " + str(slot_nr) + ", input data = " + input_fifo)
        led_start = input_fifo.find(LED_HEADER)
        if led_start != -1:
            self.leds.do_slot(slot_nr, input_fifo[led_start + len(LED_HEADER):led_start + len(LED_HEADER) +
                              configuration.NR_LEDS])
        do_start = input_fifo.find(DO_HEADER)
        if do_start != -1:
            self.digital_outputs.do_slot(slot_nr, input_fifo[do_start + len(DO_HEADER):do_start + len(DO_HEADER) +
                                         configuration.NR_DOS])

    def thread_scheduler(self):
        logging.info("Thread thread_scheduler starting")
        # create FIFO to TX data to simulator (blocking call)
        self.fifo_app_to_sim = create_w_fifo(FILE_NAME_FIFO_APP_TO_SIM, self.__event.evt_close_app)
        # create FIFO to RX data from simulator (blocking call)
        self.fifo_sim_to_app = create_r_fifo(FILE_NAME_FIFO_SIM_TO_APP, self.__event.evt_close_app)
        # set event to indicate that the fifos have been connected
        self.__event.evt_fifos_connected.set()
        # set outbound pipe to WAIT (for establishing the connection it was initially set to NOWAIT)
        win32pipe.SetNamedPipeHandleState(self.fifo_app_to_sim, win32pipe.PIPE_WAIT, None, None)
        # wait until device is powered on
        while self.__event.evt_power_on.is_set() is False:
            time.sleep(configuration.POLL_DELAY_SEC)
        # Reset for RESET_FOR_CLOCK_PERIODS after connection and device power on
        win32file.WriteFile(self.fifo_app_to_sim, str.encode(configuration.CLOCK_INDEX + ":1," +
                            configuration.RESET_INDEX + ":1,\r\n"))
        win32file.ReadFile(self.fifo_sim_to_app, FIFO_READ_BUFFER_SIZE)
        for i in range(0, configuration.RESET_FOR_CLOCK_PERIODS):
            if self.CLOCK_PERIOD_SEC[0] > 0:
                time.sleep(self.CLOCK_PERIOD_SEC[0])
            win32file.WriteFile(self.fifo_app_to_sim, str.encode(configuration.CLOCK_INDEX + ":0,\r\n"))
            win32file.ReadFile(self.fifo_sim_to_app, FIFO_READ_BUFFER_SIZE)
            if self.CLOCK_PERIOD_SEC[0] > 0:
                time.sleep(self.CLOCK_PERIOD_SEC[0])
            win32file.WriteFile(self.fifo_app_to_sim, str.encode(configuration.CLOCK_INDEX + ":1,\r\n"))
            win32file.ReadFile(self.fifo_sim_to_app, FIFO_READ_BUFFER_SIZE)
        win32file.WriteFile(self.fifo_app_to_sim, str.encode(configuration.RESET_INDEX + ":0,\r\n"))
        win32file.ReadFile(self.fifo_sim_to_app, FIFO_READ_BUFFER_SIZE)
        # variables
        self.start_time_abs = 0
        self.clock_periods = 0
        self.nr_cycles = 0
        # main loop
        while self.__event.evt_close_app.is_set() is False:
            # process signals (STEP, RUN, RUN_FOR_TIME)
            ###########################################
            if self.__event.evt_pause.is_set() is False:
                # restart? e.g. after changing the clock period
                if self.restart is True:
                    self.restart = False
                    self.start_time_abs = 0
                    self.clock_periods = 0
                    self.nr_cycles = 0
                # start time
                if self.start_time_abs == 0:
                    self.start_time_abs = time.time_ns()
                report = False
                # which time slot?
                # clock raising edge
                ####################
                if self.time_slot == SLOT_CLOCK_RAISING_EDGE:
                    # tx/rx signals
                    win32file.WriteFile(self.fifo_app_to_sim,
                                        str.encode(REPORT_CLOCK_HIGH +
                                        self.reset.do_slot(SLOT_CLOCK_RAISING_EDGE) +
                                        self.buttons.do_slot(SLOT_CLOCK_RAISING_EDGE) +
                                        self.switches.do_slot(SLOT_CLOCK_RAISING_EDGE) +
                                        self.digital_inputs.do_slot(SLOT_CLOCK_RAISING_EDGE) + "\r\n"))
                    line = win32file.ReadFile(self.fifo_sim_to_app, FIFO_READ_BUFFER_SIZE)
                    temp_line_str = str(line[1], 'utf-8')
                    # process input signals (output signals from the point of view of the FPGA)
                    if temp_line_str != "*":
                        self.do_slot(SLOT_CLOCK_RAISING_EDGE, temp_line_str)
                    # increment clock periods
                    self.clock_periods = self.clock_periods + 1
                    self.nr_cycles = self.nr_cycles + 1
                # clock high level
                ##################
                elif self.time_slot == SLOT_CLOCK_HIGH_LEVEL:
                    # gather signals
                    reset_signal = self.reset.do_slot(SLOT_CLOCK_HIGH_LEVEL)
                    if reset_signal != "":
                        report = True
                    digital_inputs_signal = self.digital_inputs.do_slot(SLOT_CLOCK_HIGH_LEVEL)
                    if digital_inputs_signal != "":
                        report = True
                    buttons_signal = self.buttons.do_slot(SLOT_CLOCK_HIGH_LEVEL)
                    if buttons_signal != "":
                        report = True
                    switches_signal = self.switches.do_slot(SLOT_CLOCK_HIGH_LEVEL)
                    if switches_signal != "":
                        report = True
                    # tx/rx signals
                    if report is True:
                        win32file.WriteFile(self.fifo_app_to_sim, str.encode(reset_signal +
                                            buttons_signal + switches_signal + digital_inputs_signal + "\r\n"))
                    else:
                        win32file.WriteFile(self.fifo_app_to_sim, str.encode("\r\n"))
                    line = win32file.ReadFile(self.fifo_sim_to_app, FIFO_READ_BUFFER_SIZE)
                    temp_line_str = str(line[1], 'utf-8')
                    # process input signals (output signals from the point of view of the FPGA)
                    if temp_line_str != "*":
                        self.do_slot(SLOT_CLOCK_HIGH_LEVEL, temp_line_str)
                # clock falling edge
                ####################
                elif self.time_slot == SLOT_CLOCK_FALLING_EDGE:
                    # tx/rx signals
                    win32file.WriteFile(self.fifo_app_to_sim,
                                        str.encode(REPORT_CLOCK_LOW +
                                        self.reset.do_slot(SLOT_CLOCK_FALLING_EDGE) +
                                        self.buttons.do_slot(SLOT_CLOCK_FALLING_EDGE) +
                                        self.switches.do_slot(SLOT_CLOCK_FALLING_EDGE) +
                                        self.digital_inputs.do_slot(SLOT_CLOCK_FALLING_EDGE) + "\r\n"))
                    line = win32file.ReadFile(self.fifo_sim_to_app, FIFO_READ_BUFFER_SIZE)
                    temp_line_str = str(line[1], 'utf-8')
                    # process input signals (output signals from the point of view of the FPGA)
                    if temp_line_str != "*":
                        self.do_slot(SLOT_CLOCK_FALLING_EDGE, temp_line_str)
                    # handle run to time
                    ####################
                    if self.remaining_clock_periods_to_run > 0:
                        self.remaining_clock_periods_to_run = self.remaining_clock_periods_to_run - 1
                        if (self.remaining_clock_periods_to_run % (
                                configuration.ESTIMATED_CLOCK_SIMULATION_RATE /
                                configuration.GUI_UPDATE_RATE_IN_HZ)) == 0:
                            # update GUI
                            self.__event.evt_gui_remain_run_time_update.set()
                        # if time expired then pause
                        if self.remaining_clock_periods_to_run == 0:
                            self.__event.evt_pause.set()
                            self.__event.evt_resume.clear()
                # clock low level
                #################
                else:  # elif self.time_slot == SLOT_CLOCK_LOW_LEVEL:
                    # gather output signals
                    reset_signal = self.reset.do_slot(SLOT_CLOCK_LOW_LEVEL)
                    if reset_signal != "":
                        report = True
                    digital_inputs_signal = self.digital_inputs.do_slot(SLOT_CLOCK_LOW_LEVEL)
                    if digital_inputs_signal != "":
                        report = True
                    buttons_signal = self.buttons.do_slot(SLOT_CLOCK_LOW_LEVEL)
                    if buttons_signal != "":
                        report = True
                    switches_signal = self.switches.do_slot(SLOT_CLOCK_LOW_LEVEL)
                    if switches_signal != "":
                        report = True
                    # tx/rx signals
                    if report is True:
                        win32file.WriteFile(self.fifo_app_to_sim, str.encode(reset_signal +
                                            buttons_signal + switches_signal + digital_inputs_signal + "\r\n"))
                    else:
                        win32file.WriteFile(self.fifo_app_to_sim, str.encode("\r\n"))
                    line = win32file.ReadFile(self.fifo_sim_to_app, FIFO_READ_BUFFER_SIZE)
                    temp_line_str = str(line[1], 'utf-8')
                    # process input signals (output signals from the point of view of the FPGA)
                    if temp_line_str != "*":
                        self.do_slot(SLOT_CLOCK_LOW_LEVEL, temp_line_str)
                # increment time slot
                self.time_slot = (self.time_slot + 1) % TIME_SLOTS
            # PAUSE
            #######
            if self.__event.evt_pause.is_set() is True:
                self.remaining_clock_periods_to_run = 0
                while (self.__event.evt_resume.is_set() is False) and \
                        (self.__event.evt_close_app.is_set() is False):
                    time.sleep(configuration.POLL_DELAY_SEC)
                if self.__event.evt_do_step.is_set() is True:
                    self.__event.evt_resume.clear()
            # STEP
            ######
            elif self.__event.evt_do_step.is_set() is True:
                self.remaining_clock_periods_to_run = 0
                if (self.time_slot == SLOT_CLOCK_FALLING_EDGE) and (not self.stepping):
                    self.stepping = True
                elif (self.time_slot == SLOT_CLOCK_RAISING_EDGE) and self.stepping:
                    self.stepping = False
                    self.__event.evt_do_step.clear()  # step done!
                    # signal GUI thread that we go to PAUSE
                    self.__event.evt_pause.set()
                if self.CLOCK_PERIOD_SEC[0] > 0:
                    while (self.__event.evt_clock.is_set() is False) and \
                            (self.__event.evt_close_app.is_set() is False):
                        time.sleep(configuration.POLL_DELAY_SEC)
                    self.__event.evt_clock.clear()
            # RUN, RUN_FOR_TIME
            ###################
            else:
                # 1 second elapsed? -> update clock simulation frequency in Hz
                if self.nr_cycles == configuration.ESTIMATED_CLOCK_SIMULATION_RATE:
                    end_time = time.time_ns()
                    diff = end_time - self.start_time_abs
                    if diff != 0:
                        self.simulation_frequency = \
                            configuration.ESTIMATED_CLOCK_SIMULATION_RATE / (diff / 1000000000)
                    self.start_time_abs = end_time
                    self.nr_cycles = 0
                # wait for clock signal or continue if TURBO mode
                #################################################
                if self.CLOCK_PERIOD_SEC[0] > 0:
                    while (self.__event.evt_clock.is_set() is False) and \
                            (self.__event.evt_close_app.is_set() is False):
                        # 1/10th as polling-error is acceptable
                        time.sleep(self.CLOCK_PERIOD_SEC[0] / (configuration.TIME_SLOTS*10))
                    self.__event.evt_clock.clear()
        logging.info("Thread thread_scheduler finished!")
