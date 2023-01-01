
# LOGGING_LEVEL specifies the lowest-severity log message a logger will handle, where debug is the lowest built-in
# severity level and critical is the highest built-in severity.
# For example, if the severity level is INFO, the logger will handle only INFO, WARNING, ERROR, and CRITICAL messages
# and will ignore DEBUG messages.
LOGGING_LEVEL = "logging.INFO"

# GUI update rate (20Hz is usually ok, but don't set it to a value greater than your monitor can display!)
GUI_UPDATE_RATE_IN_HZ = 20

# NOTE: set this value only for TURBO mode!
#       in other cases, this value is automatically adapted in clock.py as 1/CLOCK_PERIOD_EXTERNAL
#       in order to update the actual rate on the GUI every "1 second"
ESTIMATED_CLOCK_SIMULATION_RATE: int = 10000  # 22000

# WARNING: this value may have an important effect on simulation performance!
#          values below (1/GUI_UPDATE_RATE_IN_HZ) are not recommended
POLL_DELAY_SEC: float = 0.05  # 0.1  # 0.5

# nr. of widgets on board (as in VHDL)
NR_BUTTONS = 6
NR_SWITCHES = 6
NR_DIS = 10
NR_DOS = 10
NR_LEDS = 12
# nr. of sync and async DIs
NR_ASYNC_DIS = 5
assert(NR_ASYNC_DIS <= NR_DIS)
NR_SYNC_DIS = NR_DIS - NR_ASYNC_DIS

# indexes of elements (as in VHDL)
# out FIFO data
CLOCK_INDEX = "0"
RESET_INDEX = "1"
BUTTON_INDEX = "2"
SWITCH_INDEX = "3"
DI_INDEX = "4"
# in FIFO data
DO_INDEX = "0"
LED_INDEX = "1"
# NOTE: adapt buffer sizes depending on above definitions,
#       buffer sizes may hold "several" messages of the form "ID:DATA,"
FIFO_WRITE_BUFFER_SIZE = 256
FIFO_READ_BUFFER_SIZE = 256

FIFO_PATH = "\\\\.\\pipe\\"

RUN_FOR_CLOCK_PERIODS: int = ESTIMATED_CLOCK_SIMULATION_RATE
# reset automatically for RESET_FOR_CLOCK_PERIODS after connection and device power on
RESET_FOR_CLOCK_PERIODS: int = int(ESTIMATED_CLOCK_SIMULATION_RATE/100)

#############################################################################
# OK:
# CLOCK_PERIOD_EXTERNAL = "1000000000 ns" # 1 sec = 1 Hz
# CLOCK_PERIOD_EXTERNAL = "10000000 ns" # 10 ms = 0.1 kHz
#############################################################################
# NOK:
# CLOCK_PERIOD_EXTERNAL = "1000000 ns" # 1 ms = 1.0 kHz (get 330Hz instead)
# CLOCK_PERIOD_EXTERNAL = "100000 ns" # 0.1 ms = 10.0 kHz (get 330Hz instead)
#############################################################################
# OK:
CLOCK_PERIOD_EXTERNAL = "0 ns"  # TURBO
#############################################################################

CLOCK_PERIOD_EXTERNAL_MIN_MS = 0.1  # takes effect only when CLOCK_PERIOD_EXTERNAL is not zero

##################################
#
#        |<---1 period-->|
#         ___1____        ___1_...
#        |       |       |
#        0       2       0
#  ...___|       |___3___|
#
TIME_SLOTS = 4
SLOT_CLOCK_RAISING_EDGE = 0
SLOT_CLOCK_HIGH_LEVEL = 1
SLOT_CLOCK_FALLING_EDGE = 2
SLOT_CLOCK_LOW_LEVEL = 3
##################################
