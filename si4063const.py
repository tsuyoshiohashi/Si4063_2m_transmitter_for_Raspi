# si4063const.py
# parameters for Si4063.py

# Chip name
NAME_CHIPS = {0x4063}

# GPIO pin config
# si4063_name - BCM# - raspi_IO_pin#
GPIO0 = 13  # GPIO13 = pin33
GPIO1 = 6   # GPIO6 = pin31
GPIO2 = 27  # GPIO27 = pin13
GPIO3 = 17  # GPIO17 = pin11
GPIOSDN = 4 # GPIO4 = pin7
GPIOnIRQ = 5   # GPIO05 = pin29

# SoftSPI (NOT BCM system SPI)
GPIO_nSEL = 8   # GPIO8 = pin24
GPIO_SDI = 10    # GPIO10 = pin19
GPIO_SDO = 9    # GPIO9 = pin21
GPIO_SCLK = 11   # GPIO11 = pin23

# Config GPIO
GPIO_TX_DATA = GPIO0 
GPIO_CTS = GPIO1
GPIO_SHDN = GPIOSDN

# Commands
CMD_NOP = 0x00
CMD_PART_INFO = 0x01
CMD_POWER_UP = 0x02
CMD_SET_PROPERTY = 0x11
CMD_GET_PROPERTY = 0x12
CMD_GPIO_PIN_CFG = 0x13
CMD_REQUEST_DEVICE_STATE = 0x33
CMD_CHANGE_STATE = 0x34
CMD_READ_CMD_BUFF = 0x44
CMD_START_TX = 0x31
CMD_GET_ADC_READING = 0x14

# States
STATE_NOCHANGE = 0
STATE_SLEEP = 1
STATE_SPI_ACTIVE = 2
STATE_READY = 3
STATE_TX_TUNE = 5
STATE_TX = 7

# API
FREQ_XTAL = 30000000  # 30MHz

OUT_DIV_2M = 24     # 142-175MHz
OUT_DIV_70CM = 8    # 420-525MHz
FVCO_DIV_24 = 5     # 3.6GHz/24=150MHz
FVCO_DIV_8 = 2      # 3.6GHz/8 =450MHz

DIV_BY_2 = 1    # High performance
DIV_BY_4 = 0    # Low-pwer mode

HP_FINE = 1     # Lower power,fine step size, 4063?
HP_COARSE = 2   # High power, large step size, 4063?

EXT_TX_RAMP_DIS = 0 # disable ext tx ramp signal
EXT_TX_RAMP_EN = 1  # enable ext tx ramp signal

CLKDUTY_DIFF_50 = 0     # High-power(4463/4464)
CLKDUTY_SINGLE_25 = 3   # Low-poower(4460)

DIRECT_MOD_TYPE_ASYNC = 1
DIRECT_MOD_TYPE_SYNC = 0

MOD_SOURCE_DIRECT = 1
MOD_SOURCE_PSEUDO = 2
MOD_SOURCE_PACKET = 0

# Modulation types
MOD_TYPE_CW = 0
MOD_TYPE_OOK = 1
MOD_TYPE_2FSK = 2
MOD_TYPE_FSK = 2

# GPIO Mode (part)
PULL_CTL = 0x40     # bit6
GPIO_MODE_NOTHING = 0    # 
GPIO_MODE_TRISTATE = 1   #
GPIO_MODE_DRIVE0 = 2     # Low output
GPIO_MODE_DRIVE1 = 3     # High output
GPIO_MODE_INPUT = 4      # Input for TX DATA in Direct mode
GPIO_MODE_CTS = 8
GPIO_MODE_INV_CTS = 9   
GPIO_MODE_CMD_OVERLAP = 10
GPIO_MODE_SDO = 11
GPIO_MODE_POR = 12
GPIO_MODE_EN_PA = 15
GPIO_MODE_TX_DATA_CLK = 16
GPIO_MODE_IN_SPEEP = 28
GPIO_MODE_TX_STATE = 32
GPIO_MODE_LOW_BATT = 36

# Properties
#  Name = [Group, Index, Size]
GLOBAL_XO_TUNE = [0x00, 0x00, 1]
GLOBAL_CLK_CFG = [0x00, 0x01, 1]
GLOBAL_CONFIG = [0x00, 0x03, 1]

INT_CTL_ENABLE = [0x01, 0x00, 1]

PREAMBLE_TX_LENGTH = [0x10, 0x00, 1]

SYNC_CONFIG = [0x11, 0x00, 1]

MODEM_MOD_TYPE = [0x20, 0x00, 1]
MODEM_DATA_RATE = [0x20, 0x03, 3]
MODEM_TX_NCO_MODE = [0x20, 0x06, 4]
MODEM_FREQ_DEV = [0x20, 0x0a, 3]
MODEM_FREQ_OFFSET = [0x20, 0x0d, 2]
MODEM_CLKGEN_BAND = [0x20, 0x51, 1]

PA_MODE = [0x22, 0x00, 1]
PA_PWR_LVL = [0x22, 0x01, 1]
PA_BIAS_CLKDUTY = [0x22, 0x02, 1]

SYNTH_PFDCP_CPFF = [0x23, 0x00, 1]
SYNTH_PFDCP_CPINT = [0x23, 0x01, 1]
SYNTH_VCO_KV = [0x23, 0x02, 1]

FREQ_CONTROL_INTE = [0x40, 0x00, 1]
FREQ_CONTROL_FRAC = [0x40, 0x01, 3]

###