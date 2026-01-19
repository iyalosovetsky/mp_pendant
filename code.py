import microcontroller
#microcontroller.cpu.frequency = 120000000
print(microcontroller.cpu.frequency)

import board
import array
import usb.core
import usb_host

import sys
import supervisor
import time
import adafruit_usb_host_descriptors 
#from adafruit_sdcard import SDCard
import os

import digitalio
import busio
#import storage

from grblstate import GrblState, SmartKbd
from waveST7789 import WaveST7789
neo = WaveST7789()


#sd_cs = digitalio.DigitalInOut(board.GP22)
#sd_cs.direction = digitalio.Direction.OUTPUT
#sd_cs.value = True

 
#sdcard = SDCard(neo.spi, sd_cs,1000000)
#vfs = storage.VfsFat(sdcard)
#try:  
#    storage.mount(vfs, "/sd")
#except:
#    print('can not mount /sd')



pp=usb_host.Port(board.GP26, board.GP27)

#uartMPG = busio.UART(board.GP0, board.GP1, baudrate=115200)
#UART_BUF_SIZE=1960/2
UART_BUF_SIZE=1960
uartMPG = busio.UART(board.GP0, board.GP1, baudrate=115200, receiver_buffer_size=UART_BUF_SIZE)

#usbDescDemo()

#Pico-ResTouch-LCD-3.5
#SDIO_CLK	GP5	SCK pin of SDIO interface, clock input for slave device
#LCD_DC	GP8	Data/Command control pin (High: data; Low: command)
#LCD_CS	GP9	Chip select pin of LCD (Low active)
#LCD_CLK	GP10	SPI CLK pin, clock input for slave device
#MOSI	GP11	SPI MOSI, data input for slave device
#MISO	GP12	SPI MISO pin, data output for slave device
#LCD_BL	GP13	LCD backlight control
#LCD_RST	GP15	LCD reset pin (Low active)
#TP_CS	GP16	Touch controller chip select pin (Low active)
#TP_IRQ	GP17	Touch controller interrupt pin (Low active)
#SDIO_CMD	GP18	SDIO CMD pin
#D0	GP19	SDIO D0 pin
#D1	GP20	SDIO D1 pin
#D2	GP21	SDIO D2 pin
#SD_CS/D3	GP22	SDIO CS/D3 pin
  
  



kbd=SmartKbd()
st = GrblState(kbd=kbd, uart_grbl_mpg = uartMPG,neo=neo )
kbd.objGrblStateSetter(st)



start_time_cmd = time.monotonic() 

DEBUG = True
buf=array.array('B', [0 for i in range(UART_BUF_SIZE)] )

import gc

# Call the garbage collector to free up unused memory
gc.collect()

# Get the amount of free memory in bytes
free_memory = gc.mem_free()

# Print the free memory
print(f"Free memory: {free_memory} bytes")


#buf2=array.array('B', [0 for i in range(UART_BUF_SIZE)] )
while True:
  try:  
    st.query4MPG()
    if st.need_query:
        st.send2grblOne('?') # get status from grbl cnc machine
    #mpgConsole=uartMPG.read(UART_BUF_SIZE)    
    rr=uartMPG.readinto(buf)
    #rr2=-1
    if rr is not None and rr>0:
      #st.displayState("".join(map(chr, buf[:rr])))
      #st.displayState("".join(map(chr, buf)))
      
      #for i in range(UART_BUF_SIZE):
      #    if buf[i]==0:
      #        break
      #    rr2=i  
          
      #if rr2>-1:
          #sss=
          st.displayState("".join(map(chr, buf[:rr])))
          # Get the amount of free memory in bytes
          #free_memory = gc.mem_free()

          # Print the free memory
          #print(f"Free memory: {free_memory} bytes")
          
          #if DEBUG:
          #  print('mpgConsole: partial',"".join(map(chr, buf[:rr])))
          #if st._state_code!='part' and DEBUG:
          #  print('mpgConsole: ',st._state_code,sss+chr(10)+chr(10))
            
            
            
            
    # if mpgConsole is not None and mpgConsole!='': 
    #     if DEBUG:
    #         print('mpgConsole:',mpgConsole.decode())
    #     st.displayState(mpgConsole.decode())


    proceedCh=''    
    while supervisor.runtime.serial_bytes_available:
        try:
            ss=sys.stdin.read(1)
            proceedCh += ss
            if ss=='>' and DEBUG:
              print('ss:',ss)
                
        except:
            pass    
    if proceedCh!='':
        if DEBUG:
            print('proceedCh:',proceedCh,[ord(res) for res in proceedCh])
        kbd.proceedChars(proceedCh, DEBUG)
    if time.monotonic()-start_time_cmd>0.2:
        st.popCmd2grbl()
        start_time_cmd = time.monotonic()    
    #time.sleep(0.1)
  except KeyboardInterrupt:
      if DEBUG:
          break
      else:    
        print('main: will cancel')
        st.send2grblOne('cancel')       
        
            

  
#-----------------------------------------------

print("boot end.")
time.sleep(5)
#splash = displayio.Group()
#display.root_group = splash
#odb = displayio.OnDiskBitmap('/purple.bmp')
#face = displayio.TileGrid(odb, pixel_shader=odb.pixel_shader)
#splash.append(face)
#display.refresh()
# Draw a label
#text_group = displayio.Group(scale=2, x=57, y=120)
#text = "Hello World!"
#text_area = label.Label(terminalio.FONT, text=text, color=0xFFFF00)
#text_group.append(text_area)  # Subgroup for text scaling
#splash.append(text_group)

 





#display.refresh()
##^