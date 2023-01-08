import tkinter as tk
from tkinter import messagebox
import logging
import configuration
from ui.mainWindow import MainWindow


def init_config():
    # set logging level as defined in configuration
    logging_level = logging.INFO
    if configuration.LOGGING_LEVEL == "logging.DEBUG":
        logging_level = logging.DEBUG
    if configuration.LOGGING_LEVEL == "logging.INFO":
        logging_level = logging.INFO
    if configuration.LOGGING_LEVEL == "logging.WARNING":
        logging_level = logging.WARNING
    if configuration.LOGGING_LEVEL == "logging.ERROR":
        logging_level = logging.ERROR
    if configuration.LOGGING_LEVEL == "logging.CRITICAL":
        logging_level = logging.CRITICAL
    # NOTE: parameter force since python 3.8
    logging.basicConfig(format='%(asctime)s.%(msecs)03d %(levelname)s {%(module)s} [%(funcName)s] %(message)s',
                        datefmt='%H:%M:%S', level=logging_level, force=True)
    # start logger
    logging.info("set logging level to " + configuration.LOGGING_LEVEL)
    # configuration checks
    if configuration.RUN_FOR_CLOCK_PERIODS <= 0.0:
        # NOTE: hardcoded rescue value.
        configuration.RUN_FOR_CLOCK_PERIODS = int(configuration.ESTIMATED_CLOCK_SIMULATION_RATE / 100)
        logging.error("RUN_FOR_CLOCK_PERIODS shall be greater than zero. "
                      "Now set to value = " + str(configuration.RUN_FOR_CLOCK_PERIODS))
        tk.messagebox.showerror(title="ERROR",
                                message="RUN_FOR_CLOCK_PERIODS shall be greater than zero. Now set to value = " +
                                        str(configuration.RUN_FOR_CLOCK_PERIODS))
    if configuration.POLL_DELAY_SEC < (1 / configuration.GUI_UPDATE_RATE_IN_HZ):
        logging.warning("POLL_DELAY_SEC below 1/GUI_UPDATE_RATE_IN_HZ is not recommended!")
        tk.messagebox.showwarning(title="WARNING",
                                  message="POLL_DELAY_SEC below 1/GUI_UPDATE_RATE_IN_HZ is not recommended!")
    # TODO: add further plausibility checks on configuration definitions


def main():
    # init configuration
    init_config()
    # Tkinter stuff
    # use TopLevel() i.o. Tk() to avoid problems with paths
    root = tk.Toplevel()  # tk.Tk()
    root.title('FPGA hardware simulation framework 2.0')
    root.geometry("1000x600")
    root.resizable(False, False)
    app = MainWindow(root)
    app.run()


if __name__ == '__main__':
    main()
    logging.info("main() left!")
