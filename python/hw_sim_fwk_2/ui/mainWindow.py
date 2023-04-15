import pathlib
from tkinter import messagebox, PhotoImage, END, DISABLED, NORMAL
import tkinter as tk
import init
import pygubu
import logging
import configuration
import functools
import threading
import oclock
from clock import Clock
from scheduler import Scheduler
from reset import Reset
from buttons import Buttons
from switches import Switches
from digital_inputs import DigitalInputs
from digital_outputs import DigitalOutputs
from voltage_output import VoltageOutput
from leds import Leds
import time
import os


CURRENT_PATH = pathlib.Path(__file__).parent
# script or .exe?
runningScript = os.path.basename(__file__)
# we get different relative paths if we debug or run the executable file
if runningScript == "mainWindow.py":
    # .py script
    CURRENT_PATH = str(CURRENT_PATH.resolve()) + "\\"
else:
    # .exe file
    CURRENT_PATH = str(CURRENT_PATH.resolve())[:-2]
CURRENT_UI = CURRENT_PATH + "mainWindow.ui"


SIM_STATE_PAUSE = 0
SIM_STATE_RUN = 1
SIM_STATE_RUN_FOR_TIME = 2
SIM_STATE_STEP = 3


class Event:
    evt_power_on = oclock.Event()
    evt_set_reset_high = oclock.Event()
    evt_set_button_pressed = []
    evt_set_switch_right = []
    evt_fifos_connected = oclock.Event()
    evt_pause = oclock.Event()
    evt_resume = oclock.Event()
    evt_do_step = oclock.Event()
    # NOTE: we use oclock.Event.wait(timeout) i.o. time.sleep(timeout) otherwise the main thread is blocked.
    #       The following event is never set, it's only used to wait on it up to timeout and not block the main thread.
    evt_wake_up = oclock.Event()
    evt_clock = oclock.Event()
    evt_close_app = oclock.Event()
    evt_clock_finished = oclock.Event()
    # events for circuitjs
    # NOTE: using a bool flag instead, seems to NOT be affected by the value of POLL_DELAY_SEC_CIRCUITJS
    #       as much as events are affected (e.g. evt_time_message_received)
    evt_time_message_received = oclock.Event()
    evt_vo_message_send = oclock.Event()
    # these events improve performance by indicating exactly when the GUI shall update which widgets.
    # NOTE: using individual events for each of the DIs and DOs to "fine tune" GUI update decreases performance!
    evt_gui_di_websocket_connected = oclock.Event()
    evt_gui_di_websocket_disconnected = oclock.Event()
    evt_gui_di_update = oclock.Event()
    evt_gui_do_update = oclock.Event()
    evt_gui_vo_update = oclock.Event()
    evt_gui_temperature_update = oclock.Event()
    evt_gui_int_out_update = oclock.Event()
    evt_gui_led_update = oclock.Event()
    evt_gui_remain_run_time_update = oclock.Event()


# object/instance
event = Event()


class MainWindow:
    # flags and counters
    CLOCK_PERIOD_SEC = [0]
    cnt_updates = 0
    # peripheral and app objects
    clock = None
    digital_inputs = None
    digital_outputs = None
    voltage_output = None
    leds = None
    reset = None
    switches = None
    buttons = None
    scheduler = None
    # widgets
    mainWindow = None
    button_wdg = []
    button_pressed = []
    button_lbl = []
    switch_wdg = []
    switch_right = []
    switch_lbl = []
    di_wdg = []
    do_wdg = []
    led_wdg = []
    led_lbl = []

    # references to specific peripheral and app objects to be passed to scheduler as a single parameter
    class RefScheduler:
        clock = None
        digital_inputs = None
        digital_outputs = None
        voltage_output = None
        leds = None
        reset = None
        switches = None
        buttons = None        

    # object/instance
    ref_scheduler = RefScheduler()

    def __init__(self, master):
        # master is root
        ################
        self.master = master
        self.master.protocol("WM_DELETE_WINDOW", self.on_closing)
        # load init file
        ################
        init.InitApp()
        for i in range(0, configuration.NR_BUTTONS):
            event.evt_set_button_pressed.append(oclock.Event())
        for i in range(0, configuration.NR_SWITCHES):
            event.evt_set_switch_right.append(oclock.Event())
        # pygubu designer stuff
        #######################
        # Create a builder and setup resources path
        self.builder = builder = pygubu.Builder()
        builder.add_resource_path(CURRENT_PATH)
        # Load ui file
        builder.add_from_file(CURRENT_UI)
        # Create the mainWindow
        self.mainWindow = builder.get_object('mainWindow', master)
        # Connect callbacks
        builder.connect_callbacks(self)
        # other stuff
        #############
        # get images
        self.img_power_on = PhotoImage(file=CURRENT_PATH + "power_on.png")
        self.img_power_off = PhotoImage(file=CURRENT_PATH + "power_off.png")
        self.img_jmp_on = PhotoImage(file=CURRENT_PATH + "jmp_on.png")
        self.img_jmp_off = PhotoImage(file=CURRENT_PATH + "jmp_off.png")
        self.img_btn_up = PhotoImage(file=CURRENT_PATH + "btn_up.png")
        self.img_btn_down = PhotoImage(file=CURRENT_PATH + "btn_down.png")
        self.img_sw_left = PhotoImage(file=CURRENT_PATH + "sw_left.png")
        self.img_sw_right = PhotoImage(file=CURRENT_PATH + "sw_right.png")
        self.img_led_red_on = PhotoImage(file=CURRENT_PATH + "led_red_on.png")
        self.img_led_red_off = PhotoImage(file=CURRENT_PATH + "led_red_off.png")
        self.img_led_green_on = PhotoImage(file=CURRENT_PATH + "led_green_on.png")
        self.img_led_green_off = PhotoImage(file=CURRENT_PATH + "led_green_off.png")
        self.img_run = PhotoImage(file=CURRENT_PATH + "run.png")
        self.img_pause = PhotoImage(file=CURRENT_PATH + "pause.png")
        self.img_step = PhotoImage(file=CURRENT_PATH + "step.png")
        self.img_run_for_time = PhotoImage(file=CURRENT_PATH + "run_for_time.png")
        # get widgets
        self.btn_power = self.builder.get_object('btn_power', self.master)
        self.btn_reset = self.builder.get_object('btn_reset', self.master)
        self.lbl_reset = self.builder.get_object('lbl_reset', self.master)
        self.entry_clk_period_ms = self.builder.get_object('entry_clk_period', self.master)
        self.btn_run_pause = self.builder.get_object('btn_run_pause', self.master)
        self.btn_step = self.builder.get_object('btn_step', self.master)
        self.btn_run_for_time = self.builder.get_object('btn_run_for_time', self.master)
        self.btn_keep_pressed = self.builder.get_object('btn_keep_pressed', self.master)
        self.led_gui = self.builder.get_object('led_gui', self.master)
        self.frm_btns = self.builder.get_object('frm_btns', self.master)
        self.frm_btns_lbls = self.builder.get_object('frm_btns_lbls', self.master)
        self.frm_sws = self.builder.get_object('frm_sws', self.master)
        self.frm_sws_lbls = self.builder.get_object('frm_sws_lbls', self.master)
        self.frm_leds = self.builder.get_object('frm_leds', self.master)
        self.frm_leds_lbls = self.builder.get_object('frm_leds_lbls', self.master)
        self.frm_leds_2 = self.builder.get_object('frm_leds_2', self.master)
        self.frm_leds_lbls_2 = self.builder.get_object('frm_leds_lbls_2', self.master)
        self.lbl_sim_freq = self.builder.get_object('lbl_sim_freq', self.master)
        self.entry_run_for_clock_periods = self.builder.get_object('entry_run_for_clock_periods', self.master)
        self.entry_run_for_clock_periods.delete(0, END)
        self.entry_run_for_clock_periods.insert(0, str(configuration.RUN_FOR_CLOCK_PERIODS))
        self.lbl_remaining_clock_periods = self.builder.get_object('lbl_remaining_clock_periods', self.master)
        self.lbl_remaining_clock_periods['text'] = str(configuration.RUN_FOR_CLOCK_PERIODS)
        #
        self.btn_dis_circuitjs = self.builder.get_object('btn_dis_circuitjs', self.master)
        self.btn_dis_file = self.builder.get_object('btn_dis_file', self.master)
        self.btn_dis_rnd = self.builder.get_object('btn_dis_rnd', self.master)
        self.btn_dis_cnt = self.builder.get_object('btn_dis_cnt', self.master)
        if configuration.DO_DIS == configuration.DO_FILE_DIS:
            self.btn_dis_file['state'] = NORMAL
        elif configuration.DO_DIS == configuration.DO_CIRCUITJS_DIS:
            self.btn_dis_circuitjs['state'] = NORMAL
        elif configuration.DO_DIS == configuration.DO_CNT_DIS:
            self.btn_dis_cnt['state'] = NORMAL
        elif configuration.DO_DIS == configuration.DO_RND_DIS:
            self.btn_dis_rnd['state'] = NORMAL
        #
        self.scale_di = self.builder.get_object('scale_di', self.master)
        self.scale_di["state"] = NORMAL
        self.scale_di.set(configuration.DO_DIS)
        self.scale_di["state"] = DISABLED
        # variables
        self.btn_keep_pressed_is_true = False
        self.simulation_state = SIM_STATE_PAUSE
        event.evt_pause.set()
        self.gui_led_on = False
        self.websocket_connection_open = False
        # create and place additional "configurable" widgets
        # buttons
        for i in range(configuration.NR_BUTTONS):
            # buttons
            self.button_pressed.append(False)
            self.button_wdg.append(tk.Button(self.frm_btns))
            self.button_wdg[i].configure(
                borderwidth=0,
                background="#00865a",
                activebackground="#00865a",
                highlightthickness=0,
                image=self.img_btn_up,
                overrelief="flat",
                relief="flat",
                text='button' + str(i))
            self.button_wdg[i].pack(pady=5, expand="true", fill="both", side="top")
            # callbacks for buttons
            self.button_wdg[i].bind("<ButtonPress>", functools.partial(self.on_button_pressed, i), add="")
            self.button_wdg[i].bind("<ButtonRelease>", functools.partial(self.on_button_released, i), add="")
            # labels for buttons
            self.button_lbl.append(tk.Label(self.frm_btns_lbls))
            self.button_lbl[i].configure(
                background="#00865a",
                font="{Arial} 10 {}",
                foreground="#ffffff",
                text='B ' + str(i))
            self.button_lbl[i].pack(pady=4.5, expand="true", fill="both", side="top")
        # switches
        for i in range(configuration.NR_SWITCHES):
            # switches
            self.switch_right.append(False)
            self.switch_wdg.append(tk.Button(self.frm_sws))
            self.switch_wdg[i].configure(
                borderwidth=0,
                background="#00865a",
                activebackground="#00865a",
                highlightthickness=0,
                image=self.img_sw_left,
                overrelief="flat",
                relief="flat",
                text='switch' + str(i))
            self.switch_wdg[i].pack(pady=7, expand="true", fill="both", side="top")
            # callbacks for switches
            self.switch_wdg[i].bind("<ButtonPress>", functools.partial(self.on_switch_pressed, i), add="")
            # labels for switches
            self.switch_lbl.append(tk.Label(self.frm_sws_lbls))
            self.switch_lbl[i].configure(
                background="#00865a",
                font="{Arial} 10 {}",
                foreground="#ffffff",
                text='S ' + str(i))
            self.switch_lbl[i].pack(pady=4.5, expand="true", fill="both", side="top")
        # digital inputs
        for i in range(configuration.NR_DIS):
            self.di_wdg.append(tk.Label(self.mainWindow))
            self.di_wdg[i].configure(
                background="#ffE500",
                font="{Arial} 10 {}",
                foreground="#000000",
                text='U')
            self.di_wdg[i].place(anchor="nw", relx=0.4815, rely=0.6905, x=-(i * 19), y=0)
        # thread to update websocket connection status
        if configuration.DO_DIS == configuration.DO_CIRCUITJS_DIS:
            thread = threading.Thread(name="thread_websocket_state", target=self.thread_websocket_state)
            thread.start()
        # digital outputs
        for i in range(configuration.NR_DOS):
            self.do_wdg.append(tk.Label(self.mainWindow))
            self.do_wdg[i].configure(
                background="#ffE500",
                font="{Arial} 10 {}",
                foreground="#000000",
                text='U')
            self.do_wdg[i].place(anchor="nw", relx=0.787, rely=0.6905, x=-(i * 19), y=0)
        # LEDs
        for i in range(configuration.NR_LEDS):
            # LEDs
            if i < (configuration.NR_LEDS / 2):
                self.led_wdg.append(tk.Button(self.frm_leds))
            else:
                self.led_wdg.append(tk.Button(self.frm_leds_2))
            self.led_wdg[i].configure(
                borderwidth=0,
                background="#00865a",
                activebackground="#00865a",
                highlightthickness=0,
                image=self.img_led_red_off,
                overrelief="flat",
                relief="flat",
                text='led' + str(i))
            self.led_wdg[i].pack(pady=10, expand="true", fill="both", side="top")
            # callbacks for LEDs
            # -
            # labels for LEDs
            if i < 6:
                self.led_lbl.append(tk.Label(self.frm_leds_lbls))
            else:
                self.led_lbl.append(tk.Label(self.frm_leds_lbls_2))
            self.led_lbl[i].configure(
                background="#00865a",
                font="{Arial} 10 {}",
                foreground="#ffffff",
                text='L ' + str(i))
            self.led_lbl[i].pack(pady=4.5, expand="true", fill="both", side="top")
        # initial button states
        #######################
        self.set_ctrl_btns(DISABLED)
        # GUI thread
        ############
        gui_thread = threading.Thread(name="gui_thread", target=self.gui_thread)
        gui_thread.start()
        # instantiate objects
        #####################
        self.clock = Clock(event, self.CLOCK_PERIOD_SEC)  # NOTE: CLOCK_PERIOD_SEC is set within this call!
        # initialize GUI entry to current valid value (after calling Clock())
        self.entry_clk_period_ms.delete(0, END)
        self.entry_clk_period_ms.insert(0, str(self.CLOCK_PERIOD_SEC[0] * 1000))
        self.reset = Reset(event)
        self.leds = Leds(event)
        self.switches = Switches(event)        
        self.digital_inputs = DigitalInputs(event, self.CLOCK_PERIOD_SEC)
        self.digital_outputs = DigitalOutputs(event)
        self.voltage_output = VoltageOutput(event)
        self.buttons = Buttons(event)
        # fill "after" objects have been created
        self.ref_scheduler.clock = self.clock
        self.ref_scheduler.digital_inputs = self.digital_inputs
        self.ref_scheduler.digital_outputs = self.digital_outputs
        self.ref_scheduler.voltage_output = self.voltage_output
        self.ref_scheduler.leds = self.leds
        self.ref_scheduler.reset = self.reset
        self.ref_scheduler.switches = self.switches
        self.ref_scheduler.buttons = self.buttons
        # instantiate scheduler
        #######################
        self.scheduler = Scheduler(event, self.CLOCK_PERIOD_SEC, self.ref_scheduler)
        self.scheduler.remaining_clock_periods_to_run = int(configuration.RUN_FOR_CLOCK_PERIODS)

    def close_application(self):
        event.evt_close_app.set()
        event.evt_power_on.clear()
        # wait for thread to indicate that it really has finished!
        while event.evt_clock_finished.is_set() is False:
            time.sleep(configuration.POLL_DELAY_SEC)
        # wait some more for the separate event loop for websockets to react to the close_app event
        if configuration.DO_DIS == configuration.DO_CIRCUITJS_DIS:
            time.sleep(3)
        # quit + destroy
        self.master.quit()
        self.master.destroy()

    def on_closing(self):
        if self.websocket_connection_open is True:
            if tk.messagebox.askokcancel("Warning!",
                                         "Websocket connection open.\n"
                                         "The application may not close properly.\n"
                                         "Do you want to close anyway?"):
                self.close_application()
        elif tk.messagebox.askokcancel("Quit", "Do you want to quit?"):
            self.close_application()

    def run(self):
        # blocking call
        self.mainWindow.mainloop()
        logging.info("exit main loop")

    def gui_thread(self):
        logging.info("thread gui_thread started")
        while event.evt_close_app.is_set() is False:
            # NOTE: here we could subtract the time spent in update_gui() to be more accurate
            time.sleep(1 / configuration.GUI_UPDATE_RATE_IN_HZ)
            self.update_gui()
        logging.info("thread gui_thread finished")

    def update_gui(self):
        if event.evt_power_on.is_set():
            # update simulation (clock) frequency
            if self.cnt_updates == configuration.GUI_UPDATE_RATE_IN_HZ:
                self.cnt_updates = 0
                self.lbl_sim_freq['text'] = str(int(self.scheduler.simulation_frequency)) + " Hz"
            self.cnt_updates = self.cnt_updates + 1
            # toggle GUI LED
            if self.simulation_state != SIM_STATE_PAUSE:
                if self.gui_led_on is False:
                    self.gui_led_on = True
                    self.led_gui.config(image=self.img_led_green_on)
                    self.led_gui.image = self.img_led_green_on
                else:
                    self.gui_led_on = False
                    self.led_gui.config(image=self.img_led_green_off)
                    self.led_gui.image = self.img_led_green_off
            # update remaining time when running for time
            if event.evt_gui_remain_run_time_update.is_set():
                event.evt_gui_remain_run_time_update.clear()
                self.lbl_remaining_clock_periods['text'] = str(self.scheduler.remaining_clock_periods_to_run)
            # output LEDs
            if event.evt_gui_led_update.is_set():
                event.evt_gui_led_update.clear()
                for i in range(configuration.NR_LEDS):
                    if self.leds.LED_ON[i] == 1:
                        # WORKAROUND: so long we test example with f1 and f2 out
                        if (i > 4) & (i < 11):
                            self.led_wdg[i+1].config(image=self.img_led_red_on)
                            self.led_wdg[i+1].image = self.img_led_red_on
                        else:
                            self.led_wdg[i].config(image=self.img_led_red_on)
                            self.led_wdg[i].image = self.img_led_red_on
                    else:
                        # WORKAROUND: so long we test example with f1 and f2 out
                        if (i > 4) & (i < 11):
                            self.led_wdg[i+1].config(image=self.img_led_red_off)
                            self.led_wdg[i+1].image = self.img_led_red_off
                        else:
                            self.led_wdg[i].config(image=self.img_led_red_off)
                            self.led_wdg[i].image = self.img_led_red_off
            # digital inputs
            if event.evt_gui_di_update.is_set():
                event.evt_gui_di_update.clear()
                for i in range(configuration.NR_DIS):
                    self.di_wdg[i]['text'] = self.digital_inputs.get_dis(i)
            # digital outputs
            if event.evt_gui_do_update.is_set():
                event.evt_gui_do_update.clear()
                for i in range(configuration.NR_DOS):
                    self.do_wdg[i]['text'] = self.digital_outputs.get_dos(i)

    def thread_websocket_state(self):
        logging.info("thread thread_websocket_state started")
        while event.evt_close_app.is_set() is False:
            if event.evt_gui_di_websocket_connected.is_set():
                event.evt_gui_di_websocket_connected.clear()
                self.websocket_connection_open = True
                self.btn_dis_circuitjs['borderwidth'] = 7
            elif event.evt_gui_di_websocket_disconnected.is_set():
                event.evt_gui_di_websocket_disconnected.clear()
                self.websocket_connection_open = False
                self.btn_dis_circuitjs['borderwidth'] = 0
            time.sleep(configuration.POLL_DELAY_SEC)
        logging.info("thread thread_websocket_state finished!")

    def set_ctrl_btns(self, state):
        self.btn_reset["state"] = state
        self.btn_run_pause["state"] = state
        self.btn_step["state"] = state
        self.btn_run_for_time["state"] = state

    def keep_pressed_on_btn_pressed(self, _):
        if self.btn_keep_pressed_is_true is False:
            self.btn_keep_pressed_is_true = True
            self.btn_keep_pressed.config(image=self.img_jmp_on)
            self.btn_keep_pressed.image = self.img_jmp_on  # to prevent garbage collection from deleting the image
        else:
            self.btn_keep_pressed_is_true = False
            self.btn_keep_pressed.config(image=self.img_jmp_off)
            self.btn_keep_pressed.image = self.img_jmp_off  # to prevent garbage collection from deleting the image

    def on_button_pressed(self, btn_idx, _):
        if self.button_pressed[btn_idx] is False:
            # press
            self.button_pressed[btn_idx] = True
            event.evt_set_button_pressed[btn_idx].set()
            self.button_wdg[btn_idx].config(image=self.img_btn_down)
            self.button_wdg[btn_idx].image = self.img_btn_down
        elif self.btn_keep_pressed_is_true:
            # toggle
            self.button_pressed[btn_idx] = False
            event.evt_set_button_pressed[btn_idx].clear()
            self.button_wdg[btn_idx].config(image=self.img_btn_up)
            self.button_wdg[btn_idx].image = self.img_btn_up

    def on_button_released(self, btn_idx, _):
        if self.btn_keep_pressed_is_true is False:
            # toggle
            if self.button_pressed[btn_idx] is False:
                self.button_pressed[btn_idx] = True
                event.evt_set_button_pressed[btn_idx].set()
                self.button_wdg[btn_idx].config(image=self.img_btn_down)
                self.button_wdg[btn_idx].image = self.img_btn_down
            else:
                self.button_pressed[btn_idx] = False
                event.evt_set_button_pressed[btn_idx].clear()
                self.button_wdg[btn_idx].config(image=self.img_btn_up)
                self.button_wdg[btn_idx].image = self.img_btn_up

    def on_switch_pressed(self, sw_idx, _):
        if self.switch_right[sw_idx] is False:
            self.switch_right[sw_idx] = True
            event.evt_set_switch_right[sw_idx].set()
            self.switch_wdg[sw_idx].config(image=self.img_sw_right)
            self.switch_wdg[sw_idx].image = self.img_sw_right
        else:
            self.switch_right[sw_idx] = False
            event.evt_set_switch_right[sw_idx].clear()
            self.switch_wdg[sw_idx].config(image=self.img_sw_left)
            self.switch_wdg[sw_idx].image = self.img_sw_left

    def on_btn_run_pause_pressed(self, _):
        # TODO: check why we need to check the state of the button
        if self.btn_run_pause["state"] == NORMAL:
            if (self.simulation_state == SIM_STATE_RUN) or (self.simulation_state == SIM_STATE_RUN_FOR_TIME):
                event.evt_pause.set()
                event.evt_resume.clear()
                self.simulation_state = SIM_STATE_PAUSE
                self.btn_run_pause.config(image=self.img_run)
                self.btn_run_pause.image = self.img_run
            else:
                event.evt_pause.clear()
                event.evt_resume.set()
                self.simulation_state = SIM_STATE_RUN
                self.btn_run_pause.config(image=self.img_pause)
                self.btn_run_pause.image = self.img_pause
            self.btn_run_for_time["state"] = NORMAL

    def thread_on_do_step(self):
        while event.evt_pause.is_set() is False:
            time.sleep(configuration.POLL_DELAY_SEC)
        self.simulation_state = SIM_STATE_PAUSE

    def on_btn_step_pressed(self, _):
        # TODO: check why we need to check the state of the button
        if self.btn_run_pause["state"] == NORMAL:
            if (self.simulation_state == SIM_STATE_RUN) or (self.simulation_state == SIM_STATE_RUN_FOR_TIME):
                event.evt_resume.clear()
            else:
                event.evt_resume.set()
            self.simulation_state = SIM_STATE_STEP
            event.evt_pause.clear()
            event.evt_do_step.set()
            self.btn_run_pause.config(image=self.img_run)
            self.btn_run_pause.image = self.img_run
            self.btn_run_for_time["state"] = NORMAL
            # launch thread to process event evt_pause which is set after evt_do_step.clear()
            thread_on_do_step_finished = threading.Thread(name="thread_on_do_step_finished",
                                                          target=self.thread_on_do_step)
            thread_on_do_step_finished.start()

    def thread_on_run_for_time(self):
        while event.evt_pause.is_set() is False:
            time.sleep(configuration.POLL_DELAY_SEC)
        # Run for time paused or stepped?
        if self.scheduler.remaining_clock_periods_to_run != 0:
            self.scheduler.remaining_clock_periods_to_run = 0
        self.simulation_state = SIM_STATE_PAUSE
        self.btn_run_pause.config(image=self.img_run)
        self.btn_run_pause.image = self.img_run
        # re-enable button
        if event.evt_power_on.is_set():
            self.btn_run_for_time["state"] = NORMAL

    def on_btn_run_for_time_pressed(self, _):
        # TODO: check why we need to check the state of the button
        if self.btn_run_pause["state"] == NORMAL:
            self.simulation_state = SIM_STATE_RUN_FOR_TIME
            self.btn_run_pause.config(image=self.img_pause)
            self.btn_run_pause.image = self.img_pause
            self.btn_run_for_time["state"] = DISABLED
            # trigger the scheduler by setting remaining_clock_periods_to_run
            self.scheduler.remaining_clock_periods_to_run = int(configuration.RUN_FOR_CLOCK_PERIODS)
            event.evt_resume.set()
            event.evt_pause.clear()
            # launch thread to process event evt_pause
            thread_on_run_for_time = threading.Thread(name="thread_on_run_for_time",
                                                      target=self.thread_on_run_for_time)
            thread_on_run_for_time.start()

    def on_btn_power_pressed(self, _):
        if event.evt_power_on.is_set():
            if (self.simulation_state == SIM_STATE_RUN) or (self.simulation_state == SIM_STATE_RUN_FOR_TIME):
                self.simulation_state = SIM_STATE_PAUSE
                event.evt_pause.set()
                event.evt_resume.clear()
                self.btn_run_pause.config(image=self.img_run)
                self.btn_run_pause.image = self.img_run
            event.evt_power_on.clear()
            self.btn_power.config(image=self.img_power_on)
            self.btn_power.image = self.img_power_on
            self.set_ctrl_btns(DISABLED)
            self.gui_led_on = False
            self.led_gui.config(image=self.img_led_green_off)
            self.led_gui.image = self.img_led_green_off
        else:
            if event.evt_fifos_connected.is_set() is True:
                event.evt_power_on.set()
                self.btn_power.config(image=self.img_power_off)
                self.btn_power.image = self.img_power_off
                self.set_ctrl_btns(NORMAL)
            else:
                tk.messagebox.showinfo(message="Please start the VHDL simulator first!")

    def on_btn_reset_pressed(self, _):
        # TODO: check why we need to check the state of the button
        if self.btn_run_pause["state"] == NORMAL:
            if event.evt_set_reset_high.is_set():
                event.evt_set_reset_high.clear()
                self.lbl_reset.config(text="RESET: low")
            else:
                event.evt_set_reset_high.set()
                self.lbl_reset.config(text="RESET: high")

    def on_key_press_entry_clk_period(self, evt):
        if evt.char == '\r':
            temp_clock_period_ms = self.entry_clk_period_ms.get()
            try:
                temp_clock_period_ms_f = float(temp_clock_period_ms)
                self.clock.set_clock_period_ms(temp_clock_period_ms_f)
                self.scheduler.restart_counters()
                logging.debug("new clock period = " + temp_clock_period_ms + " ms")
            except Exception as e:
                logging.error("invalid clock period: " + temp_clock_period_ms + " ms - exception: " + str(e))
                # restore GUI entry to current valid value
                self.entry_clk_period_ms.delete(0, END)
                self.entry_clk_period_ms.insert(0, str(self.CLOCK_PERIOD_SEC[0] * 1000))

    def on_key_pressed_run_for_clock_periods(self, evt):
        if evt.char == '\r':
            temp_run_for_clock_periods = self.entry_run_for_clock_periods.get()
            try:
                int(temp_run_for_clock_periods)  # temp_run_for_clock_periods_i = int(temp_run_for_clock_periods)
                configuration.RUN_FOR_CLOCK_PERIODS = temp_run_for_clock_periods
                logging.debug("new run for clock periods = " + temp_run_for_clock_periods)
            except Exception as e:
                logging.error("invalid run for clock periods: "
                              + temp_run_for_clock_periods + " - exception: " + str(e))
                # restore GUI entry to current valid value
                self.entry_run_for_clock_periods.delete(0, END)
                self.entry_run_for_clock_periods.insert(0, str(configuration.RUN_FOR_CLOCK_PERIODS))
            # update remaining clock periods also
            self.scheduler.remaining_clock_periods_to_run = int(configuration.RUN_FOR_CLOCK_PERIODS)
            self.lbl_remaining_clock_periods['text'] = str(self.scheduler.remaining_clock_periods_to_run)
