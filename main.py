from machine import UART
import machine
import time
import sys

from nanoguilib.color_setup import ssd
from nanoguilib.nanogui import refresh
from TermReader import TermReader
from ns2009 import Touch


print(machine.freq()) 
# Set CPU to 240 MHz
machine.freq(240000000)
# Verify the new frequency
print(machine.freq()) 

# Initialize UART (adjust parameters for your board/pins)
# Example for a Raspberry Pi Pico (UART 0 on GP0/GP1)
uartMPG = UART(0, baudrate=115200, tx=0, rx=1) 

# Alternatively, for Pyboard (adjust port/pins as needed)
# from pyb import UART
# uart = UART(1, 9600) 

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

#from LCD_2inch8 import LCD_2inch8
#lcd = LCD_2inch8()
#lcd.bl_ctrl(100)
#lcd.fill(lcd.BLACK)
#lcd.show_up()

refresh(ssd, True)

st = GrblState(uart_grbl_mpg = uartMPG,neo=ssd,debug=False )
st.set_rotary_obj(rot0,0,'x',1.0)
rot0.add_listener(st.rotary_listener0)


    
kbd.objGrblStateSetter(st)

refresh(ssd)


term_reader = TermReader(sys.stdin.buffer)
print('display started')

ns = Touch()
ns.set_int_handler(st.touchscreen_press)
print('touch initialized')



#  File "grblUartState.py", line 108, in uart_callback
#  File "grblUartState.py", line 1099, in procUartInByte
# File "grblUartState.py", line 111, in uart_callback
#MemoryError: memory allocation failed, allocating 9042 bytes


while True:
    #st.query4MPG()
    st.p_RTLoop()
    # if st.need_query:
    #     st.send2grblOne('?') # get status from grbl cnc machine    
        
    if st.neo_refresh:
        st.neo_refresh=False
        refresh(ssd)##
        
    proceedCh = term_reader.read()
    if proceedCh is not None and len(proceedCh)>0:
        if DEBUG:
            print('proceedCh:',proceedCh,[ord(res) for res in proceedCh])
        kbd.proceedChars(proceedCh, False)
        
            
    time.sleep(0.1) # Small delay to prevent a hard loop
