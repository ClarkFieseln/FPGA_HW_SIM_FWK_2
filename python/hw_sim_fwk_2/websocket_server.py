from autobahn.asyncio.websocket import WebSocketServerProtocol, WebSocketServerFactory
import asyncio
import threading
import time
import logging
import configuration


MAX_ABS_DO_V = 0.5
SWITCH_PERIOD_SEC = 5.0
DO_AUTO_SWITCH = True
input_data_f = 0  # DO voltage of input node in circuitjs
switch = False  # ext voltage to control analog switch in circuitjs
__event = None
__loop = None
__update_di_sync = None
__update_di_async = None

# example:
# the websocket server connects to circuitjs to read simulated voltage values while
# the analog switch is switched periodically from here
class WebSocketServer(WebSocketServerProtocol):

    def __init__(self):
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

    @staticmethod
    def get_switch():
        global switch
        return switch

    @staticmethod
    def set_switch_on(state):
        global switch
        switch = state

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

    def onMessage(self, payload, is_binary):
        global input_data_f
        global __update_di_sync
        global __update_di_async
        decoded = payload.decode('utf8')
        input_data_f = float(decoded)
        __update_di_sync()
        __update_di_async()
        logging.debug("Text message received: {0}".format(decoded))

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
