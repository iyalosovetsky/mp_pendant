from machine import UART
import time
import sys

from nanoguilib.color_setup import ssd
from nanoguilib.nanogui import refresh
from TermReader import TermReader

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

DEBUG = False

#from LCD_2inch8 import LCD_2inch8
#lcd = LCD_2inch8()
#lcd.bl_ctrl(100)
#lcd.fill(lcd.BLACK)
#lcd.show_up()

refresh(ssd, True)

st = GrblState(uart_grbl_mpg = uartMPG,neo=ssd,debug=True )
kbd.objGrblStateSetter(st)

refresh(ssd)


term_reader = TermReader(sys.stdin.buffer)
print('display started')




while True:
    st.query4MPG()
    #l=st.procUartGetLastData(printEnable=True)
    if st.need_query:
        st.send2grblOne('?') # get status from grbl cnc machine    
        
    if st.neo_refresh:
        st.neo_refresh=False
        refresh(ssd)
        
    proceedCh = term_reader.read()
    if proceedCh is not None and len(proceedCh)>0:
        if DEBUG:
            print('proceedCh:',proceedCh,[ord(res) for res in proceedCh])
        kbd.proceedChars(proceedCh, False)
    if time.time_ns()-start_time_cmd>200000000: #0.2s
        st.popCmd2grbl()
        start_time_cmd = time.time_ns()  
        
            
    time.sleep(0.1) # Small delay to prevent a hard loop
