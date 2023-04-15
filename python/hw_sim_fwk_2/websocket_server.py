import math
from autobahn.asyncio.websocket import WebSocketServerProtocol, WebSocketServerFactory
import asyncio
import threading
import time
import logging
import configuration


MAX_ABS_DO_V = 1.2  # NOTE: Vs-peak-normal + noise-peak
MAX_OUT_V = 10.0
SWITCH_PERIOD_SEC = 0.01
DO_AUTO_SWITCH = False
VO_SEND = False
MAX_SEQ_NR = 2**8
timestamp_ms = 0
input_data_f = 0  # Ve voltage of input node in circuitjs
switch = False
output_voltage = 0  # ext voltage to control analog switch in circuitjs
output_frequency = 27000.0  # 27000 to 32000
__event = None
__loop = None
__update_di_sync = None
__update_di_async = None
global_self = None
# NOTE: using a bool flag seems to be less affected by sleep() than real events
evt_time_message_received = False


# the websocket server connects to circuitjs to read simulated voltage values while
class WebSocketServer(WebSocketServerProtocol):
    seqNrRx = 0
    seqNrTx = 0
    # NOTE: init timestamp_ms with a different value than the initial timestamp received in telegram
    timestamp_ms = 7777

    def __init__(self):
        global global_self
        global_self = self
        
        logging.info("WebSocketServer initializing..")
        super().__init__()

    @staticmethod
    async def thread_on_close_app():
        logging.info("thread_on_close_app started")
        global __event
        global __loop
        # monitor close app event
        while __event.evt_close_app.is_set() is False:
            await asyncio.sleep(configuration.POLL_DELAY_SEC)
        # stop event loop
        __loop.stop()
        logging.info("thread_on_close_app finished!")

    @staticmethod
    def websocket_thread(event, update_di_sync, update_di_async):
        # websocket code using own asyncio event loop
        global __event
        global __loop
        global __update_di_sync
        global __update_di_async
        __event = event
        __loop = asyncio.new_event_loop()
        __update_di_sync = update_di_sync
        __update_di_async = update_di_async
        asyncio.set_event_loop(__loop)
        # websocket
        factory = WebSocketServerFactory("ws://127.0.0.1:9000")
        factory.protocol = WebSocketServer
        coro = __loop.create_server(factory, '0.0.0.0', 9000)
        server = __loop.run_until_complete(coro)
        # monitoring task to react to app close event
        monitoring_close_app_coro = __loop.create_task(WebSocketServer.thread_on_close_app())
        asyncio.ensure_future(monitoring_close_app_coro)
        # loop
        try:
            # infinite loop
            __loop.run_forever()
        finally:
            server.close()
            __loop.close()

    # return normalized value between 0 and 1
    @staticmethod
    def get_normalized_input_data():
        global input_data_f
        return (MAX_ABS_DO_V + input_data_f)/(2.0*MAX_ABS_DO_V)
    
    # return current timestamp in ms
    @staticmethod
    def get_timestamp_ms():
        global timestamp_ms
        return timestamp_ms

    @staticmethod
    def get_switch():
        global switch
        return switch

    @staticmethod
    def set_switch_on(state):
        global switch
        switch = state

    @staticmethod
    def set_output_voltage(value):
        global output_voltage
        output_voltage = value        

    @staticmethod
    def set_output_frequency(value):
        global output_frequency
        output_frequency = value

    def onConnect(self, request):
        logging.info("Client connecting: {0}".format(request.peer))

    def onOpen(self):
        logging.info("Connection open.")
        # update GUI
        global __event
        __event.evt_gui_di_websocket_connected.set()
        # start separate thread to control switch in circuitjs automatically (as an example)
        if DO_AUTO_SWITCH:
            thread = threading.Thread(target=self.switch_thread)
            thread.start()
        # start separate thread to send output voltage
        if VO_SEND:
            thread = threading.Thread(target=self.vo_thread)
            thread.start()
            
    @staticmethod
    def gotNewMessage():
        global evt_time_message_received
        retVal = evt_time_message_received
        if evt_time_message_received is True:
            evt_time_message_received = False
        return retVal

    def onMessage(self, payload, is_binary):
        global input_data_f
        global timestamp_ms
        global __update_di_sync
        global __update_di_async    
        global __event
        global evt_time_message_received
        decoded = payload.decode('utf8')
        # decode telegram here as a string "<seqNr>,<timestamp_ms>,<input_data_f>"
        decoded = decoded.split(',')
        decodedRight = decoded[1].split(';')
        seqNrRx = int(decoded[0])
        if self.seqNrRx == seqNrRx:       
            self.seqNrRx = (self.seqNrRx + 1)%MAX_SEQ_NR
            timestamp_ms = float(decodedRight[0])
            input_data_f = float(decodedRight[1])     
            # we may get repeated telegrams (same contents incl. timestamp but new seqNr)
            # so, avoid at least unnecessary calls to __update_di_sync() and __update_di_async()
            if (self.timestamp_ms != timestamp_ms):
                self.timestamp_ms = timestamp_ms
                __update_di_sync()
                __update_di_async()   
            else:
                logging.debug("repeated timestamp_ms = " + decodedRight[0])
            # NOTE: bool not affected by sleep() as much as real events
            # __event.evt_time_message_received.set()   
            evt_time_message_received = True            
            logging.debug("Text message received: {0},{1},{2}".format(decoded[0],decodedRight[0],decodedRight[1]))
        else:
            # NOTE: in any case we need to catch-up if sender is faster than us (and the prev. event got lost?)
            if self.seqNrTx == (self.seqNrRx - 1)%MAX_SEQ_NR:
                # NOTE: bool not affected by sleep() as much as real events
                # __event.evt_time_message_received.set()
                evt_time_message_received = True
            logging.warning("seqNrRx mismatsch! Text message received: {0},{1},{2}".format(decoded[0],decodedRight[0],decodedRight[1]))

    def onClose(self, was_clean, code, reason):
        logging.info("Connection closed: {0}".format(reason))
        # update GUI
        global __event
        __event.evt_gui_di_websocket_disconnected.set()

    # example of auto switch
    def switch_thread(self):
        logging.info("switch_thread started")
        global switch
        global __event
        while (self.state == WebSocketServer.STATE_OPEN) and (__event.evt_close_app.is_set() is False):            
            self.sendMessage((str(switch)).encode('utf8'), False)
            switch = not switch
            time.sleep(SWITCH_PERIOD_SEC)
        logging.info("switch_thread finished!")

    # example of output voltage
    def vo_thread(self):
        # t = 0  # NOTE: use TIME_STEP_CIRCUITJS as alternative to timestamp_ms
        logging.info("vo_thread started")
        global output_voltage
        global __event
        global timestamp_ms
        telegram = ""       
        while (self.state == WebSocketServer.STATE_OPEN) and (__event.evt_close_app.is_set() is False):
            if __event.evt_vo_message_send.is_set() is True:
                __event.evt_vo_message_send.clear()
                # TX only in sync with RX
                if self.seqNrTx == (self.seqNrRx - 1)%MAX_SEQ_NR:
                    # NOTE: use TIME_STEP_CIRCUITJS as alternative to timestamp_ms
                    # output_voltage = MAX_OUT_V*math.sin(2.0*math.pi*output_frequency*t)    
                    output_voltage = MAX_OUT_V*math.sin(2.0*math.pi*output_frequency*(timestamp_ms/1000.0))                    
                    telegram = str(self.seqNrTx) + "," + str(output_voltage)                                              
                    self.sendMessage((telegram).encode('utf8'), False)                          
                    # NOTE: use TIME_STEP_CIRCUITJS as alternative to timestamp_ms
                    # t = t + configuration.TIME_STEP_CIRCUITJS
                    self.seqNrTx = (self.seqNrTx + 1)%MAX_SEQ_NR
            else:
                time.sleep(configuration.POLL_DELAY_SEC_CIRCUITJS)
        logging.info("vo_thread finished!")
        
    @staticmethod
    def sendVoltageMessage():
        global global_self
        output_voltage = MAX_OUT_V*math.sin(2.0*math.pi*output_frequency*(timestamp_ms/1000.0))                    
        telegram = str(global_self.seqNrTx) + "," + str(output_voltage)                                              
        global_self.sendMessage((telegram).encode('utf8'), False)                          
        global_self.seqNrTx = (global_self.seqNrTx + 1)%MAX_SEQ_NR
        
        
        
        
        
