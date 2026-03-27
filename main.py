from machine import UART
import machine
import time
import sys

from nanoguilib.color_setup import ssd
from nanoguilib.nanogui import refresh
from TermReader import TermReader


import network
import socket
import json




print(machine.freq()) 
# Set CPU to 300 MHz
#machine.freq(300000000)
machine.freq(240000000) # for wifi stability, 240 MHz is more stable than 300 MHz on ESP32-S3
# Verify the new frequency
print(machine.freq()) 

# --- 1. WiFi Connection Setup ---
def connect_wifi(ssid, password):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print('Connecting to WiFi...')
        wlan.connect(ssid, password)
        while not wlan.isconnected():
            pass
    print('WiFi Connected:', wlan.ifconfig())
    return wlan.ifconfig()[0]


ip = connect_wifi('IGORNET', 'IG0RNET29041971') 


# Initialize UART (adjust parameters for your board/pins)

uartMPG = UART(0, baudrate=115200, tx=0, rx=1) 

 
from grblUartState import GrblState
from SmartKbd import SmartKbd
kbd=SmartKbd()

start_time_cmd = time.time_ns()

from rotaryIRQ import RotaryIRQ
rot0 = RotaryIRQ(pin_num_dt=27,  
    pin_num_clk=26,  
    min_val=0,  
    reverse=False,  
    range_mode=RotaryIRQ.RANGE_UNBOUNDED)

 
 
    


DEBUG = False

 

refresh(ssd, True)

st = GrblState(uart_grbl_mpg = uartMPG,neo=ssd,debug=False, templateDir='/templates')
st.gui.set_rotary_obj(rot0,0,'x',1.0)
st.gui.setYellowButton(17)
st.gui.setRedButton(16)

rot0.add_listener(st.rotary_listener0)


    
kbd.objGrblStateSetter(st)

#refresh(ssd)


term_reader = TermReader(sys.stdin.buffer)
print('display started')

#ns = Touch(isLandscape=False)
#ns.set_int_handler(st.gui.touchscreen_press)
print('touch initialized')

#p_yellow=Pin(17, Pin.IN, Pin.PULL_UP)
#p_red=Pin(16, Pin.IN, Pin.PULL_UP)
#bt_red=Button(pin=p_yellow,callback=st.button_red_callback,callback_long=st.button_red_callback_long)
#bt_yellow=Button(pin=p_red,callback=st.button_yellow_callback,callback_long=st.button_yellow_callback_long)



st.gui.start_http(ip)


while True:
 
    st.p_RTLoop()
  
        
    
        
    proceedCh = term_reader.read()
    if proceedCh is not None and len(proceedCh)>0:
        if DEBUG:
            print('proceedCh:',proceedCh,[ord(res) for res in proceedCh])
        kbd.proceedChars(proceedCh, False)
        
            
    time.sleep(0.05) # Small delay to prevent a hard loop





