# Si4063 2m transmitter for Raspi

Transmit a modulated wave in the 144Mhz band using RaspberryPi and an expansion board (si4063 2m radio hat, homemade, see hat directory).

・Frequency can be set from 144 to 146MHz

・The maximum output is 0.1W (20dBm) and can be set in 128 steps.

・CW (Continuous wave), OOK, FSK modulation is possible

・If you want to attach an antenna and actually emit radio waves, you will need an amateur radio license.

. When operating, be sure to terminate the SMA terminal (J2: RF output terminal). Otherwise, it may break.

# Environment where operation has been confirmed
Raspi3B+　Raspberry Pi OS(bookworm)

You need to install pigpio.

# HAT configuration and operation
As the title says, we use Silicon Labs' Si4063-C.

The SPI is controlled from the Raspi, but it is controlled by itself via GPIO, so there is no need to configure the SPI of the Raspi.
If SPI0 is enabled, please disable it. (Used as GPIO)

Si4063 operates in Direct Async Mode.

Transmission data is passed from the Raspi's GPIO to the Si4063's GPIO, and is transmitted at the same timing without going through the FIFO.

While transmitting, LED2 lights up as an indicator.

# Software
## si4063.py

You can perform simple sending operations by running it from the command line.

````
$ python si4063.py
````

If there are no arguments, display simple help and exit.
The arguments are as follows.

### -c (seconds)
Transmits unmodulated waves for the specified number of seconds. (10 seconds if not specified)
It is used to measure output magnitude, spurious, etc.

The transmission frequency is 144.05MHz by default. (Can be set with variables)

### -f
Transmits FSK modulated wave for about 10 seconds.

The data is 10101010....
The data rate is approximately 1000bps.
The frequency deviation is 8kHz.
These can be set with parameters.

The IC specifications support data rates up to 1Mbps.
I think high-speed communication is possible if you create an accurate baud rate using a timer interrupt. (It's a little difficult in python...)

### -o
Transmits OOK modulated wave for about 10 seconds.

The data is 10101010....
The data rate is approximately 1000bps.
Like FSK, it can be set with parameters.

Please note that si4063const.py is a parameter file. Please put it in the same directory.

## Main methods
si4063.py can be used by importing it into a python program as a module. (This is the original usage)

The main methods are shown below.

### reset()
Reset si4063.
Execute once after turning on the power.

### power_up()
Boot si4063. Use in the order of reset → power_up.

### part_info()
Get the chip number.
````
count, chip_no = si4063.part_info()
````
count: Number of times it took to retrieve (usually it can be read in one time, but if it is too many times, something is happening)

chip_no: Chip number (0x4063)

### set_radio_frequency(frequency)
Set the transmission frequency. The unit is Hz.
There may be an discrepancies of about 2Hz depending on the resolution of the synthesizer.

### set_modem_freq_offset(freq_offset)
Gives an offset to the transmit frequency.
This corrects the error in the crystal's oscillation frequency, but the value seems to vary depending on the modulation method.
The unit is Hz.

### set_pa_pwr_lvl(pwr_lvl)
Set the transmit power. Specify a value between 0x0 and 0x7f.
A graph of setting values and output can be found in Figure 8 of the si4063-C data sheet.

### setup(mod_type, freq_dev)
Configure the IC register settings and set the modulation method.

Specify either MOD_TYPE_OOK, MOD_TYPE_FSK, or MOD_TYPE_CW.

For FSK, the frequency deviation can be specified in Hz.

### start_tx()
Start sending.

### stop_tx()
Stop sending. The internal state is READY.

### tx_data(data)
Set the sending data data(0|1).
In the sending state, it will be reflected immediately.

### get_adc_reading()
Measures the IC power supply voltage and temperature.

````
temp, voltage = si4063.get_adc_reading()
````

The units are °C and V.

Please note that si4063Cconst.py is a parameter file. Please put it in the same directory.

## radio_morse.py

This is a sample app that sends Morse code.
Import and use si4063.py.

Start it by specifying the wpm number as an argument on the command line.

````
$ python radio_morse.py wpm
````

You will be asked to enter a character string, so please enter an alphanumeric character string.

Morse code '.' and '-' are displayed on the console and sent.

Please note that wpm is limited to 5 to 30.

Have A Fun!
