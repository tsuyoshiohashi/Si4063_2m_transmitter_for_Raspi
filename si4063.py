#!/usr/bin/env python3
#
# si4063.py
# driver fot raspi si4063 2m radio hat(my own work, see hat directory)
# 
# This implementation is for personal experiments.
# Copyright (c) 2023 Tsuyoshi Ohashi
# Released under the MIT license
# https://opensource.org/licenses/mit-license.php
#
# references
# https://github.com/thasti/utrak
# https://www.silabs.com/documents/public/application-notes/AN633.pdf
# https://www.silabs.com/documents/public/application-notes/EZRadioPRO_REVC2_API.zip
#
# CHIP DATA MODE : DIRECT ASYNCHRONOUS SOURCE MODE
import pigpio
import time
from si4063const import *

__version__ = "2023.12.23"

# debug flag
debug = False
#debug flag primitive
_debug = False

class Si4063:
    # configure raspi pins
    # I/O and SOFTWARE SPI
    def __init__(self):
        self.pi = pigpio.pi()
        if not self.pi.connected:
            raise Exception("Error: pigpio NOT connected")
        
        # Shutdown pin
        self.pi.set_mode(GPIO_SHDN, pigpio.OUTPUT)
        self.pi.write(GPIO_SHDN, 1)  # PIN_SHDN = High

        # GPIO_13 OUTPUT for TXDATA  
        self.pi.set_mode(GPIO_TX_DATA, pigpio.OUTPUT)
        self.pi.write(GPIO_TX_DATA, 0)  # TX_DATA = Low

        # GPIO_6 INPUT for CTS
        self.pi.set_mode(GPIO_CTS, pigpio.INPUT)
        self.pi.set_pull_up_down(GPIO_CTS, pigpio.PUD_DOWN)

        # nSEL pin
        self.pi.set_mode(GPIO_nSEL, pigpio.OUTPUT)
        self.pi.write(GPIO_nSEL, 1)  # nSEL = 1
        # SDI(MOSI) pin
        self.pi.set_mode(GPIO_SDI, pigpio.OUTPUT)
        self.pi.write(GPIO_SDI, 0)  # MOSI = 0
        # SDO(MISO) pin
        self.pi.set_mode(GPIO_SDO, pigpio.INPUT)
        self.pi.set_pull_up_down(GPIO_SDO, pigpio.PUD_DOWN) # pull down
        # SCLK pin
        self.pi.set_mode(GPIO_SCLK, pigpio.OUTPUT)
        self.pi.write(GPIO_SCLK, 0)  # SCLK = 0
    
    # Set nSEL pin Low
    def _spi_select(self):
        if(_debug):
            print("\t_select")
        self.pi.write(GPIO_nSEL, 0)
    # Set nSEL pin High
    def _spi_deselect(self):
        if(_debug):
            print("\t_deselect")
        self.pi.write(GPIO_nSEL, 1)
    # Set SCLK pin 1/0
    def _spi_clk(self, bit):
        self.pi.write(GPIO_SCLK, bit)
    
    # Write a byte
    def _spi_wr(self, data):
        if(_debug):
            print("\t_wr: {:02x}".format(data))
        for i in range(8):
            self._spi_clk(0)
            bit = 1 if((data<<(i) & 0x80)) else 0
            self.pi.write(GPIO_SDI, bit)
            self._spi_clk(1)
            
        self._spi_clk(0)
        self.pi.write(GPIO_SDI, 0)  
    
    # Read a byte
    # return : 1 byte read
    def _spi_rd(self):
        data = 0
        for i in range(8):
            self._spi_clk(0)
            data = data<<1
            self.pi.write(GPIO_SDI, 1)      # write 0xff in read
            bit = self.pi.read(GPIO_SDO)
            data += bit
            self._spi_clk(1)
        
        self._spi_clk(0)
        if(_debug):
            print("\t_rd: {:02x}".format(data))
        return data
        
    # Check CTS pin
    # return : cts(0xff or 0x00=timeout)
    def _is_CTS(self):
        timeout, cts = 1000, 0x00

        while(timeout>=0):
            bit_cts = self.pi.read(GPIO_CTS)
            if(bit_cts==1):
                cts = 0xff    
                break
            time.sleep(0.001)
            timeout -=1
        return cts
    
    # Check CTS over SPI
    # rturn : CTS(0xff), Not deselect to continue
    #         0x00,  deselect 
    def _is_CTS_spi(self):
        timeout, cts = 10, 0x00

        while(timeout>=0):
            self._spi_select()
            self._spi_wr( CMD_READ_CMD_BUFF)
            cts = self._spi_rd()
            if(cts==0xff):
                break
            self._spi_deselect()
            time.sleep(0.001)
            timeout -=1
        return cts      
    
    # Write bytes after wait CTS
    # to_send : bytes to be written
    def _write(self, to_send, desel=True):
        if(_debug):
            print("\t_Write:")
        
        #self._wait_cts(read_reply=False)
        self._is_CTS()
        self._spi_select()
        for b in to_send:
            b_as_bytes = b.to_bytes(1,byteorder="big")
            #self._wait_cts(False)
            self._spi_wr(b)
        if(desel):
            self._spi_deselect()

    # Read count size bytes after select and check CTS
    # 
    # count : qty of read data
    # desel :  deselect after read data
    # return : byte(s) read (list)
    def _read(self, count, desel=True):
        if(_debug):
            print("\t_Read:")
        self._is_CTS()
        self._spi_select()
        reply = []
        self._spi_wr(CMD_READ_CMD_BUFF)       
        for i in range(count):
            #self._wait_cts(read_reply=False)
            reply.append( self._spi_rd())           
        if(desel):
            self._spi_deselect()
        return reply
    
    # Enter Shutdown State
    def shutdown(self):
        self.pi.write(GPIO_SHDN, 1)     # PIN_SHDN = High
        time.sleep(0.001)              # Wait 100μS

    # Exit Shutdown State
    def wakeup(self):
        self.pi.write(GPIO_SHDN, 0)     # PIN_SHDN = Low
        time.sleep(0.02)                # Wait 20mS
        #self._wait_cts(read_reply=0)
        self._is_CTS()

    # Reset chip, shutdown and wake-up
    def reset(self):
        self.shutdown()
        self.wakeup()
    
    # NOP,ensure communication established
    # return : CTS(0xff or 0x00)
    def nop(self):
        self._is_CTS()
        self._spi_select()
        self._spi_wr(CMD_NOP)
        ret = self._spi_rd()
        if(debug):
            print("Nop: {:02x}".format(ret))
        self._spi_deselect()
        #self._wait_cts(False)
        return ret
        
    # power-up(boot) and set XTAL freq
    def power_up(self):
        if(debug):
            print("power_up")
        #self._wait_cts(read_reply=False)
        self._is_CTS()
        FUNC = 1    # EZRadio PRO
        TCXO = 0    # 0=XTAL, 1=ext TCXO
        
        to_send = [CMD_POWER_UP, FUNC, TCXO, 0xff & (FREQ_XTAL >> 24), 0xff & (FREQ_XTAL >> 16), 0xff & (FREQ_XTAL >> 8), 0xff & FREQ_XTAL]
        if(debug):
            print("to_send: ", ' '.join('{:02x}'.format(x) for x in to_send))
        self._write(to_send)

        time.sleep(0.01)
        #self._wait_cts(read_reply=False)
        self._is_CTS()

     # Get device info(Chip No)
     # return : count: number of times tried to read, chip_no: chip number(0x4063)
    def part_info(self):
        if(debug):
            print("part_info")
        chip_no = None
        
        self._is_CTS()
        time.sleep(0.01)
        
        self._spi_select()
        self._spi_wr(CMD_PART_INFO)
        self._spi_deselect()
        
        count = 1
        while(count<10):
            part_info = self._read(1+8, desel=True)
            if(part_info[0]==0xff):
                chip_no = (part_info[2]<<8) + part_info[3]
                if(debug):
                    print("Part_info: ", ' '.join('{:02x}'.format(x) for x in part_info))
                    print("Chip No : {:04x}".format(chip_no))
                break  
            else:
                time.sleep(0.1)
                count += 1
       
        return count, chip_no

    # Read and Convert temperature and battery voltage 
    # return : temprature, battery voltage
    def get_adc_reading(self):
        if(debug):
            print("get_adc_reading")
        #self._wait_cts(read_reply=False)
        cmd = CMD_GET_ADC_READING
        adc_en = (1<<4) | (1<<3) | (0<<2) | 0 # temperature, battery voltage, adc_gpio, adc_pin
        adc_cfg = 0x00  # Use defaults
        to_send = [cmd, adc_en, adc_cfg]
        self._write( to_send, desel=True)
        time.sleep(0.02)     # wait conversion

        reply = self._read(1+6, desel=True)
        #if(debug):
        #    print("ADC Reply: ", ' '.join('{:02x}'.format(x) for x in reply))

        if(reply[0]==0xff):
            # battery voltage
            battery_adc = (reply[3]<<8) + reply[4]        
            battery_voltage = 3*battery_adc / 1280
            if(debug):
                #print("Batt adc : {:04x}".format(battery_adc ))
                print("Battery Voltage: ", battery_voltage)
            # temprature
            temp_adc = (reply[5]<<8) + reply[6]        
            temp = (899 / 4096) * temp_adc - 293
            if(debug):
                #print("Temp adc : {:04x}".format(temp_adc ))
                print("Temprature: ", temp)
        else:
            temp, battery_voltage = None, None
        return temp, battery_voltage
    
    # Request Device State
    # return : current state
    def request_device_state(self):
        if(debug):
            print("request_device_state")
        #self._wait_cts(read_reply=False)
        self._is_CTS()
        time.sleep(0.01)
        self._spi_select()
        self._spi_wr(CMD_REQUEST_DEVICE_STATE)
        self._spi_deselect()
        
        #self._wait_cts(read_reply=True)
        dev_state = self._read(1+2, desel=True)
        if(dev_state[0]==0xff):
            #self._wait_cts(read_reply=True)
            cur_state = dev_state[1]
        else:
            cur_state = None
        if(debug):
            print("Main State: ", ' '.join('{:02x}'.format(x) for x in dev_state))
        return cur_state
    
    # Change State in State Machine
    # next_state : next state to be
    def change_state(self, next_state):
        cmd = CMD_CHANGE_STATE
        to_send = [cmd, next_state]
        self._write(to_send)
        if(debug):
            print("to_send: ", ' '.join('{:02x}'.format(x) for x in to_send))
    
    # Set a value of property
    # group : group number of property
    # index : proterty index
    # val : value to be set
    def set_property(self, group, index, val):
        command = CMD_SET_PROPERTY
        to_send = [command, group, 1, index, val]
        if(debug):
            print("Set_prop TO_SEND: ", ' '.join('{:02x}'.format(x) for x in to_send))
        self._write(to_send)
    
    # Set  values of property
    # group : group number of property
    # index : proterty index
    # vals : values to be set (list)
    def set_properties(self, group, index, vals):
        command = CMD_SET_PROPERTY
        length = len(vals)
        to_send = [command, group, length] + [index] + vals
        if(debug):
            print("Set_prop TO_SEND: ", ' '.join('{:02x}'.format(x) for x in to_send))
        #self._wait_cts(reply=False)
        self._write(to_send)
        #self._wait_cts(read_reply=False)     
    
    # Get a value of property(s)
    # prop : list, [group, index, num of property]
    # return : value(s) of property (list)
    def get_property(self, prop):
        to_send = [CMD_GET_PROPERTY, prop[0], prop[2], prop[1]]
        if(debug):
            print("Get_prop TO_SEND: ", ' '.join('{:02x}'.format(x) for x in to_send))
        self._write(to_send)
        time.sleep(0.01)
        reply = self._read( 1 + prop[2])
        if(debug):
            print("prop(s): ", ' ', ' '.join('{:02x}'.format(x) for x in reply))
        return reply[1:]
    
    # Set Xtal frequency tuning 
    def set_global_xo_tune(self):
        group, index = GLOBAL_XO_TUNE[0], GLOBAL_XO_TUNE[1]
        tune_value = 0x40       # High=7f, Low=0
        global_xo_tune = 0x7f & tune_value  # 7bits
        self.set_property(group, index, global_xo_tune)

    # Chip Operation mode setting
    def set_global_config(self):
        group, index = GLOBAL_CONFIG[0], GLOBAL_CONFIG[1]
        reserved = 0x01
        fast = 1    # quick start_tx
        fifo = 0    # split
        generic = 0 # generic protocol
        high_perf = 0  # 0=high performance TX and RX, 1=Low power mode TX and RX
        global_cfg = 0xff & ((reserved << 6) | (fast << 5) | (fifo << 4) | (generic <<1) | high_perf)
        self.set_property(group, index, global_cfg)

    # Interrupt setting
    def set_int_ctl_enable(self):
        group, index = INT_CTL_ENABLE[0], INT_CTL_ENABLE[1]
        chip_int = 0    # 0=DISABLED, 1=ENABLED
        ph_int = 0
        int_ctrl = chip_int<<2 | ph_int
        self.set_property(group, index, int_ctrl)
        
    # disable tx preamble
    def set_preamble_tx_length(self):
        group, index = PREAMBLE_TX_LENGTH[0], PREAMBLE_TX_LENGTH[1]
        tx_length = 0
        self.set_property(group, index, tx_length)

    # No transmit sync word
    def set_sync_config(self):
        group, index = SYNC_CONFIG[0], SYNC_CONFIG[1]
        sync_cfg = 0xff & (1 << 7 )  # NO_SYNC_XMIT
        self.set_property(group, index, sync_cfg)

    # Select modulation type and source (CW/OOK/FSK, ASYNC Direct mode)
    def set_modem_mod_type_direct(self, type_mod):
        group, index = MODEM_MOD_TYPE[0], MODEM_MOD_TYPE[1]
        tx_direct_mod_type = (DIRECT_MOD_TYPE_ASYNC<<7)     # 1=ASYNC, 0=SYNC
        tx_direct_mod_gpio = (0<<5)     # 0=GPIO0
        mod_source = (MOD_SOURCE_DIRECT <<3)            # 1=DIRECT, 2=PSEUDO, 0=PACKET
        if(type_mod<MOD_TYPE_CW or type_mod>MOD_TYPE_FSK):
            raise Exception("Error: MOD_TYPE")
        mod_type = 0xff & (tx_direct_mod_type | tx_direct_mod_gpio | mod_source | type_mod)
        self.set_property(group, index, mod_type)
    
    # Set Data Rate
    def set_modem_data_rate(self, data_rate):
        group, index = MODEM_DATA_RATE[0], MODEM_DATA_RATE[1]
        props = [0xff & (data_rate>>16), 0xff & (data_rate>>8), 0xff & data_rate]
        self.set_properties(group, index, props)
        
    # Setup NCO modulo and oversampling mode
    def set_modem_tx_nco_mode(self):
        group, index = MODEM_TX_NCO_MODE[0], MODEM_TX_NCO_MODE[1]   # 0x06..0x09
        txosr = 0    # 0=ENUM_0 10x
        #
        # MODEM_TX_NCO_MODE = MODEM_DATA_RATE x FREQ_XTAL / (TX_DATA_RATE x TXOSR)
        # Here, Define MODEM_DATA_RATE = TX_DATA_RATE, TXOSR = 10
        ncomod = int(FREQ_XTAL / 10)
        props = [0xff & ((txosr <<2) | (ncomod>>24)), 0xff & (ncomod >>16), 0xff & (ncomod >>8), 0xff & ncomod]
        self.set_properties(group, index, props)
    
    # Set FSK Deviation
    def set_modem_freq_dev(self, freq_dev=8333):
        group, index = MODEM_FREQ_DEV[0], MODEM_FREQ_DEV[1]   # 0x0a..0x0c
        # MODEM_FREQ_DEV = 2^19 * outdiv * desired_dev_Hz / ( Npresc * freq_xo)
        # Here, outdiv = OUTDIV_2M, Npresc = 2,
        modem_freq_dev = round( 2**19 * OUT_DIV_2M * freq_dev / (2 * FREQ_XTAL))   # 2=High performance
        if(debug):
            print(freq_dev, modem_freq_dev)
        props = [0xff & (modem_freq_dev>>16), 0xff & modem_freq_dev>>8, 0xff & modem_freq_dev]
        self.set_properties(group, index, props)

    # Set offset frequency
    def set_modem_freq_offset(self, freq_offset):
        group, index = MODEM_FREQ_OFFSET[0], MODEM_FREQ_OFFSET[1]   # 0x0d..0x0e
        # MODEM_FREQ_OFFSET = 2^19 * outdiv * desired_offset_Hz / ( Npresc * freq_xo)
        # Here, outdiv = OUTDIV_2M, Npresc = 2,
        modem_freq_offset = round( 2**19 * OUT_DIV_2M * freq_offset / (2 * FREQ_XTAL))   # 2=High performance
        props = [0xff & modem_freq_offset>>8, 0xff & modem_freq_offset]
        self.set_properties(group, index, props)

    # Set chip High performance and 2m band
    def set_modem_clkgen_band(self):
        group, index = MODEM_CLKGEN_BAND[0], MODEM_CLKGEN_BAND[1]
        sy_recal = 1<<4         # SKIP FORCE_SY_RECAL
        sy_sel = DIV_BY_2<<3      # 1=Div-by-2,High performance
        #band = FVCO_DIV_8    # 2=FVCO_DIV_8(3.6GHz/8=450MHz)
        band = FVCO_DIV_24    # 5=FVCO_DIV_24(3.6GHz/24=150MHz)
        modem_clkgen_band = sy_recal | sy_sel | band
        self.set_property(group, index, modem_clkgen_band)
        
    # Enable TX Ramp Signal and Set pa_mode HP_COARSE/SQW
    def set_pa_mode(self):
        group, index = PA_MODE[0], PA_MODE[1]
        ext_pa_ramp = EXT_TX_RAMP_EN<<7     # 1=Enable, 0=Disable tx ramp signal
        pa_sel = HP_COARSE<<2           # 2=HP_COARSE, 1=HP_FINE, 6=LowPower(Si4460), 8=MidPower(Si4461)
        #pa_sel = HP_FINE<<2           # 2=HP_COARSE, 1=HP_FINE, 6=LowPower(Si4460), 8=MidPower(Si4461)
        pa_mode = ext_pa_ramp | pa_sel  # bit0 0=Class-E/Square Wave match, 1=Switched Current Mode
        self.set_property(group, index, pa_mode)  # SQW
    
    # Configure PA output level (ddac = 0x0:min - 0x7f:max)
    def set_pa_pwr_lvl(self, ddac):
        group, index = PA_PWR_LVL[0], PA_PWR_LVL[1]
        pwr_lvl = 0x7f & ddac
        self.set_property(group, index, pwr_lvl)
        
    # Set PA duty cycle and bias current
    def set_pa_bias_clkduty(self, ob=0x0):
        group, index = PA_BIAS_CLKDUTY[0], PA_BIAS_CLKDUTY[1]
        clk_duty = CLKDUTY_DIFF_50 << 6    # 3=SINGLE_25, 0=DIFF_50
        #ob = 0x3f           # When Switched Current Mode
        bias_clkduty = 0xff & (clk_duty | ob)
        self.set_property(group, index, bias_clkduty)
    
    # Set frequency (now 2m band only)
    def set_radio_frequency(self, freq):
        debug = 0
        # Check Frequency Range
        if(debug):
            print("set_radio_frequency")
        if (freq < 144e6) or (freq > 146e6):
            raise Exception("Error: ", sys._getframe().f_code.co_name)
        ### Set Integer Divider
        group, index = FREQ_CONTROL_INTE[0], FREQ_CONTROL_INTE[1]
        outdiv = OUT_DIV_2M     # 145MHz band
        f_int_2m = 2 * FREQ_XTAL / outdiv
        f_int = int(freq / f_int_2m) - 1       # f_frac must be between 1 and 2
        self.set_property(group, index, f_int)
        ### Set Fractinal Divider
        group, index = FREQ_CONTROL_FRAC[0], FREQ_CONTROL_FRAC[1]
        f_frac = round((freq / f_int_2m - f_int) * 2**19)        
        frac19 = 0xff & (f_frac >>16)
        frac15 = 0xff & (f_frac >>8)
        frac7 = 0xff & (f_frac)
        props = [frac19, frac15, frac7]
        self.set_properties(group, index, props)

        f_out = (f_int + f_frac/2**19) * 2 * FREQ_XTAL / outdiv
        if(debug):
            print("int: {}, frac: {}".format(f_int, f_frac))
            print("props:", ' '.join('{:02x}'.format(x) for x in props))
            print("ratio(1<2): ", f_frac/2**19)
            print("freq: {}, fout: {}".format(freq, f_out))
            self.get_property(FREQ_CONTROL_INTE)
            self.get_property(FREQ_CONTROL_FRAC)

    # Set OOK / Direct mode
    def set_mod_ook(self):
        self.set_modem_mod_type_direct(MOD_TYPE_OOK)
        
    # Set FSK / Direct mode
    def set_mod_fsk(self):
        self.set_modem_mod_type_direct(MOD_TYPE_FSK, freq_dev)
    
    # Select feed forward charge pump current
    def set_synth_pfdcp_cpff(self):
        group, index = SYNTH_PFDCP_CPFF[0], SYNTH_PFDCP_CPFF[1]
        cp_ff_cur = 0x0
        pfdcp_cpff = cp_ff_cur 
        self.set_property(group, index, pfdcp_cpff)
        
    #
    # Select integration charge pump current
    def set_synth_pfdcp_cpint(self):
        group, index = SYNTH_PFDCP_CPINT[0], SYNTH_PFDCP_CPINT[1]
        cp_int_cur = 0x0    # 40
        pfdcp_cpint = cp_int_cur 
        self.set_property(group, index, pfdcp_cpint)
    
    # Set gain scaling factors(Kv)
    def set_synth_vco_kv(self):
        group, index = SYNTH_VCO_KV[0], SYNTH_VCO_KV[1]
        ### [1,1] works well ###
        kv_dir = 0x1    # 1=half, 2=max
        kv_int = 0x1    # 1=33percent, 2=66percent 3=max
        vco_kv = kv_dir<<2 + kv_int 
        self.set_property(group, index, vco_kv)        
        
    # Initialize si4063 registers. Called After Power-up
    # type_mod : modulation type, CW/OOK/FSK
    # freq_dev : FSK frequency deviation Hz
    def setup(self, type_mod, freq_dev=8333):
        if(debug):
            print("Modulation : {}".format(type_mod))
        data_rate = 64000   # DUMMY in Direct Async mode
        self.set_global_config()
        self.set_global_xo_tune()
        
        self.set_int_ctl_enable()
        
        self.set_preamble_tx_length()
        self.set_sync_config()
        
        self.set_modem_tx_nco_mode()
        self.set_modem_data_rate(data_rate)
        self.set_modem_mod_type_direct(type_mod)
        if(type_mod == MOD_TYPE_FSK):
            self.set_modem_freq_dev(freq_dev)
        self.set_modem_clkgen_band()    # Set 2m band 
        #
        bias = 0x0
        self.set_pa_bias_clkduty(bias)
        self.set_pa_mode()
        #ddac = 0x7f
        #self.set_pa_pwr_lvl(ddac)
        
        #self.set_synth_pfdcp_cpff()
        #self.set_synth_pfdcp_cpint()
        # uncomment the following if the frequency is unstable
        #self.set_synth_vco_kv()
    
    # set tx bit in direct mode
    def tx_data(self, bit):
        self.pi.write(GPIO_TX_DATA, bit & 0x01)  # TX_DATA
            
    # set tx bit toggled
    def tx_data_toggle(self):
        self.pi.write(GPIO_TX_DATA, not self.pi.read(GPIO_TX_DATA))  # TX_DATA
    
    # start transmit
    def start_tx(self):
        cmd = CMD_START_TX
        txcomplete_state = STATE_READY<<4   # 1=SLEEP, 2=SPI_ACTIVE, 3=READY
        start_timing = 0   # 0=immediate, 1=upon WUT
        condition = txcomplete_state + start_timing
        channel = 0
        tx_len = [0, 0]  # 0=Direct mode??
        to_send = [cmd, channel, condition, tx_len[1], tx_len[0], 0, 0]
        self._write(to_send)
        if(debug):
            print("to_send: ", ' '.join('{:02x}'.format(x) for x in to_send))        

    # stop transmit and set state READY
    def stop_tx(self):
        self.change_state(STATE_READY)

    # change state TX
    def enable_tx(self):
        if(debug):
            print(sys._getframe().f_code.co_name)
        self.change_state(STATE_TX)    
    
    # destructor
    def __del__(self):
        self.pi.stop()          # Stop handling pin       

# TEST
# help message 
def show_help():
    print("options: -f/-o/-c/-h")
    print("-c duration(seconds) : Transmit Continuous wave for duration" )
    print("-f : transmit fsk signal")
    print("-o : transmit ook signal")
    print("-h : Show this help")

##### TEST #####
import sys
###
if __name__ == '__main__':
    print("si4063.py ver.", __version__ )
    args = sys.argv
    try:
        cmd = args[1]
    except:
        show_help()
        exit()
    
    if(cmd == "-h" or len(args)==0 ):
        show_help()
        exit()
        
    si4063 = Si4063()    
    si4063.reset()          # Shutdown and Wake-up
    
    # Check part info
    count, chip_no = si4063.part_info()
    dots_read = '.' * count
    if(chip_no in NAME_CHIPS):
        print("Detected" + dots_read + "  {:04x}".format(chip_no))
    else:
        raise Exception(dots_read + "Error: wrong chip name {:04x}".format(chip_no))
    
    # power up sequence after POR
    si4063.power_up()
    
    # Read temerature and voltage
    temp, voltage = si4063.get_adc_reading()
    print("Temperature: {:.1f} °C".format(temp))
    print("Voltage: {:.2f} volt".format(voltage))

    # Set frequency
    radio_frequency = 144050000
    print("frequency(Hz): ", radio_frequency)
    si4063.set_radio_frequency(radio_frequency)
    
    # Set output power
    pwr_lvl = 0x3f      # up to 0x7f
    si4063.set_pa_pwr_lvl(pwr_lvl)

    # setup symbol rate
    baud = 1000
    interval = 1/baud
    duration = 10
    
    # Parse command line
    if(cmd == "-f"):
        ### FSK
        print("FSK mode")
        freq_dev = 8000
        si4063.setup(MOD_TYPE_FSK, freq_dev)
        freq_offset = 3000
        si4063.set_modem_freq_offset(freq_offset)
        si4063.start_tx()    
        for i in range(baud*duration):
            si4063.tx_data_toggle()
            time.sleep(interval)
        si4063.stop_tx()
        
    elif(cmd=="-o"):
        ### OOK
        print("OOK mode")
        si4063.setup(MOD_TYPE_OOK)
        freq_offset = -5000
        si4063.set_modem_freq_offset(freq_offset)
        si4063.start_tx()
        for i in range(baud*duration):
            si4063.tx_data_toggle()
            time.sleep(interval)
        si4063.stop_tx()
        
    elif(cmd=="-c"):
        ### CW for radio test
        print("CW mode")
        si4063.setup(MOD_TYPE_CW)
        freq_offset = 4000
        si4063.set_modem_freq_offset(freq_offset)
        si4063.start_tx()
        try:
            duration = int(args[2])
        except:
            duration = 10
        print("Duration(S): ", duration)  
        time.sleep(duration)
        si4063.stop_tx()
        
    else:
        show_help()

    del si4063
### end of si4063.py