import configuration
import logging
import tkinter


root = tkinter.Tk()
root.withdraw()


class DigitalOutputs:
    __event = None
    DOS = ['U']*configuration.NR_DOS

    def __init__(self, event):
        logging.info('init DigitalOutputs')
        self.__event = event

    # update changes "asynchronously", that is, independently of slot_nr
    def do_slot(self, _, new_value):
        self.DOS = new_value
        # inform GUI
        self.__event.evt_gui_do_update.set()

    # called from GUI
    def get_dos(self, i):
        return self.DOS[-1 - i]
