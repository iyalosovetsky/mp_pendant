from machine import UART, Pin
import machine
import time
import sys

from nanoguilib.color_setup import ssd
from nanoguilib.nanogui import refresh
from TermReader import TermReader
from ns2009 import Touch
from button import Button


print(machine.freq()) 
# Set CPU to 300 MHz
machine.freq(300000000)
# Verify the new frequency
print(machine.freq()) 

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

st = GrblState(uart_grbl_mpg = uartMPG,neo=ssd,debug=False )
st.set_rotary_obj(rot0,0,'x',1.0)
rot0.add_listener(st.rotary_listener0)


    
kbd.objGrblStateSetter(st)

refresh(ssd)


term_reader = TermReader(sys.stdin.buffer)
print('display started')

ns = Touch(isLandscape=False)
ns.set_int_handler(st.touchscreen_press)
print('touch initialized')

bt_red=Button(pin=Pin(17, Pin.IN, Pin.PULL_UP),callback=st.button_red_callback,callback_long=st.button_red_callback_long)
bt_yellow=Button(pin=Pin(16, Pin.IN, Pin.PULL_UP),callback=st.button_yellow_callback,callback_long=st.button_yellow_callback_long)


 


while True:
 
    st.p_RTLoop()
  
        
    if st.neo_refresh:
        st.neo_refresh=False
        refresh(ssd)##
        
    proceedCh = term_reader.read()
    if proceedCh is not None and len(proceedCh)>0:
        if DEBUG:
            print('proceedCh:',proceedCh,[ord(res) for res in proceedCh])
        kbd.proceedChars(proceedCh, False)
        
            
    time.sleep(0.1) # Small delay to prevent a hard loop
