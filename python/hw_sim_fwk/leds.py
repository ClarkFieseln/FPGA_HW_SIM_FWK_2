import configuration
import logging
import tkinter


root = tkinter.Tk()
root.withdraw()


class Leds:
    __event = None
    LED_ON = []  # TODO: add getter/setter

    def __init__(self, event):
        logging.info('init Leds')
        self.__event = event
        for i in range(configuration.NR_LEDS):
            self.LED_ON.append(0)

    # update changes "asynchronously", that is, independently of slot_nr
    def do_slot(self, _, new_value):
        for i in range(configuration.NR_LEDS):
            if self.LED_ON[i] == 0:
                if new_value[configuration.NR_LEDS - 1 - i] == "1":
                    logging.debug("LED %s is ON", str(i))
                    self.LED_ON[i] = 1
            else:
                # NOTE: other values like e.g. U, X will just be ignored
                if new_value[configuration.NR_LEDS - 1 - i] == "0":
                    logging.debug("LED %s is OFF", str(i))
                    self.LED_ON[i] = 0
        # inform GUI
        self.__event.evt_gui_led_update.set()
