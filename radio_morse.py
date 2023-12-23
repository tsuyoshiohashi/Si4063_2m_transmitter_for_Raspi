#!/usr/bin/env python3
#
# radio_morse.py 
# transmit morse signal w/ raspi si4063 2m radio hat(my own work, see hat directory)
# 
# This implementation is for personal experiments.
# Copyright (c) 2023 Tsuyoshi Ohashi
# Released under the MIT license
# https://opensource.org/licenses/mit-license.php
# 
import si4063 as radio
import time
import sys

__version__ = "2023.12.23"

# morse code encode table
morse_code = {
    'A': '.-', 'B': '-...', 'C': '-.-.', 'D': '-..', 'E': '.',
    'F': '..-.', 'G': '--.', 'H': '....', 'I': '..', 'J': '.---',
    'K': '-.-', 'L': '.-..', 'M': '--', 'N': '-.', 'O': '---',
    'P': '.--.', 'Q': '--.-', 'R': '.-.', 'S': '...', 'T': '-',
    'U': '..-', 'V': '...-', 'W': '.--', 'X': '-..-', 'Y': '-.--',
    'Z': '--..', '0': '-----', '1': '.----', '2': '..---', '3': '...--',
    '4': '....-', '5': '.....', '6': '-....', '7': '--...', '8': '---..',
    '9': '----.', '.': '.-.-.-', ',': '--..--', '?': '..--..', '\'': '.----.',
    '!': '-.-.--', '/': '-..-.', '(': '-.--.', ')': '-.--.-', '&': '.-...',
    ':': '---...', ';': '-.-.-.', '=': '-...-', '+': '.-.-.', '-': '-....-',
    '_': '..--.-', '"': '.-..-.', '$': '...-..-', '@': '.--.-.'
}

# convert text to morse code
# text : text to encode
# return : morse code("." and "-")
def text_to_morse(text):
    morse = ''
    for char in text.upper():
        if char in morse_code:
            morse += morse_code[char] + ' '  # Add space after char
        elif char == ' ':  # Add partition
            morse += '/ '
    return morse

# Convert unit time from wpm
# wpm : words per minute(morse speed)
def calculate_unit_time(wpm):
    return 1200 / wpm  # 5 chars/word, unit_time/char=1/5×60×1000=1200/wpm Second

# transmit radio morse code
# dot_time : time for dot (Second)
# morse_code : morse code text ("." and "-") 
def morse_code_to_ook(dot_time, morse_code):
    si4063.start_tx()
    for symbol in morse_code:
        print(symbol, end="", flush=True)
        if symbol == '.':
            si4063.tx_data(1)
            time.sleep(dot_time)
            si4063.tx_data(0)
            time.sleep(dot_time)
        elif symbol == '-':
            si4063.tx_data(1)
            time.sleep(3 * dot_time)
            si4063.tx_data(0)
            time.sleep(dot_time)
        elif symbol == ' ':
            time.sleep(3 * dot_time)
    print("")
    si4063.stop_tx()

# Send morse code converted from text
# text : text to send
# wpm : words per minute(morse speed)
def send_morse(text, wpm=10):
    
    morse_code = text_to_morse(text)
    unit_time = calculate_unit_time(wpm)/1000
    #print("wpm: ", wpm)
    print("morse code: ", morse_code)

    morse_code_to_ook(unit_time, morse_code)
    
### 
if __name__ == "__main__":
    args = sys.argv
    # morse speed is between 5 and 30 
    try:
        wpm = int(args[1])
        if(wpm>30):
            wpm = 30
        elif(wpm < 5):
            wpm = 5 
    except:
        wpm = 10
        
    print("Radio Morse Starting  ver.", __version__)
    print("radio ver.", radio.__version__)
    print("wpm: ", wpm)
    si4063 = radio.Si4063()    
    si4063.reset()          # Shutdown and Wake-up
    
    # Check part info
    count, chip_no = si4063.part_info()
    dots_read = '.' * count
    if(chip_no in radio.NAME_CHIPS):
        print("Detected" + dots_read + " {:04x}".format(chip_no))
    else:
        raise Exception(dots_read + "Error: wrong chip name {:04x}".format(chip_no))
    
    si4063.power_up()
    temperature, voltage = si4063.get_adc_reading()
    print("Temperature: {:.1f} °C".format(temperature))
    print("Voltage: {:.2f} volt".format(voltage))
    
    # set frequency
    radio_frequency = 144050000
    si4063.set_radio_frequency(radio_frequency)
    print("frequency(Hz): ", radio_frequency)
    si4063.set_modem_freq_offset(-4000)
    
    # set RF power
    pwr_lvl = 0x7f      # up to 0x7f(max)
    si4063.set_pa_pwr_lvl(pwr_lvl)
    ### OOK mode
    si4063.setup(radio.MOD_TYPE_OOK)
    
    text = input("Input text to send: ")
    send_morse(text, wpm)
    del si4063
    ###
    # end or radio_morse.py
