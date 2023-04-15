import configuration
import logging
import tkinter
from websocket_server import WebSocketServer
import math


root = tkinter.Tk()
root.withdraw()


class VoltageOutput:
    __event = None
    VO = ""
    VO_F = 0.0

    def __init__(self, event):
        logging.info('init VoltageOutput')
        self.__event = event
        self.VO = ['U'] * configuration.NR_VO_BITS

    # update changes "asynchronously" - but the VHDL code will only generate new values on raising clock edges
    def do_slot(self, _, new_value):
        if new_value != self.VO:
            self.VO = new_value
            self.VO_F = 0.0
            for i in range(0,configuration.NR_VO_BITS):
                if new_value[i] == '1':
                    self.VO_F = self.VO_F + math.pow(2,configuration.NR_VO_BITS-1-i)
            self.VO_F = self.VO_F*1000.0 # *100.0         
            logging.info("set output_voltage = " + str(self.VO_F))
            WebSocketServer.set_output_frequency(self.VO_F)
            # inform GUI
            # self.__event.evt_gui_vo_update.set()

    # called from GUI
    # def get_vo(self, i):
        # return self.VO[-1 - i]


