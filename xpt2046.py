"""XPT2046 Touch module."""
from time import sleep
from micropython import const  # type: ignore
import time
from machine import Pin,SPI,PWM


LCD_DC   = 8
LCD_CS   = 9
LCD_SCK  = 10
LCD_MOSI = 11
LCD_MISO = 12
LCD_BL   = 13
LCD_RST  = 15
TP_CS    = 16
TP_IRQ   = 17

class Touch(object):
    """Serial interface for XPT2046 Touch Screen Controller."""

    # Command constants from ILI9341 datasheet
    GET_X = const(0b11010000)  # X position 
    GET_Y = const(0b10010000)  # Y position
    GET_Z1 = const(0b10110000)  # Z1 position
    GET_Z2 = const(0b11000000)  # Z2 position
    GET_TEMP0 = const(0b10000000)  # Temperature 0
    GET_TEMP1 = const(0b11110000)  # Temperature 1
    GET_BATTERY = const(0b10100000)  # Battery monitor
    GET_AUX = const(0b11100000)  # Auxiliary input to ADC

    def __init__(self,  width=320, height=240,
                 x_min=750, x_max=3400, y_min=430, y_max=3270+430):
        """Initialize touch screen controller.

        Args:
            spi (Class Spi):  SPI interface for OLED
            cs (Class Pin):  Chip select pin
            int_pin (Class Pin):  Touch controller interrupt pin
            int_handler (function): Handler for screen interrupt
            width (int): Width of LCD screen
            height (int): Height of LCD screen
            x_min (int): Minimum x coordinate
            x_max (int): Maximum x coordinate
            y_min (int): Minimum Y coordinate
            y_max (int): Maximum Y coordinate
        """
        self.spi = None
        self.cs = Pin(TP_CS, Pin.OUT, value=1)
        
        self.cs.init(self.cs.OUT, value=1)
        self.rx_buf = bytearray(3)  # Receive buffer
        self.tx_buf = bytearray(3)  # Transmit buffer
        self.width = width
        self.height = height
        # Set calibration
        self.x_min = x_min
        self.x_max = x_max
        self.y_min = y_min
        self.y_max = y_max
        self.x_multiplier = width / (x_max - x_min)
        self.x_add = x_min * -self.x_multiplier
        self.y_multiplier = height / (y_max - y_min)
        self.y_add = y_min * -self.y_multiplier

        self.int_pin = Pin(TP_IRQ, Pin.IN)
        self.int_pin.init(self.int_pin.IN)
        self.int_handler = None
        self.int_locked = False
        self.int_pin.irq(trigger=self.int_pin.IRQ_FALLING | self.int_pin.IRQ_RISING,
                    handler=self.int_press)


    def set_int_handler(self, handler):
        """Set interrupt handler for touch events.

        Args:
            handler (function): Function to call on touch event
        """
        self.int_handler = handler 

    def get_touch(self):
        """Take multiple samples to get accurate touch reading."""
        timeout = 2  # set timeout to 2 seconds
        confidence = 5
        buff = [[0, 0] for x in range(confidence)]
        buf_length = confidence  # Require a confidence of 5 good samples
        buffptr = 0  # Track current buffer position
        nsamples = 0  # Count samples
        while timeout > 0:
            if nsamples == buf_length:
                meanx = sum([c[0] for c in buff]) // buf_length
                meany = sum([c[1] for c in buff]) // buf_length
                dev = sum([(c[0] - meanx)**2 +
                          (c[1] - meany)**2 for c in buff]) / buf_length
                if dev <= 50:  # Deviation should be under margin of 50
                    return self.normalize(meanx, meany)
            # get a new value
            sample = self.raw_touch()  # get a touch
            if sample is None:
                nsamples = 0    # Invalidate buff
            else:
                buff[buffptr] = sample  # put in buff
                buffptr = (buffptr + 1) % buf_length  # Incr, until rollover
                nsamples = min(nsamples + 1, buf_length)  # Incr. until max

            sleep(.05)
            timeout -= .05
        return None

    def int_press(self, pin):
        """Send X,Y values to passed interrupt handler."""
        if not pin.value() and not self.int_locked:
            self.int_locked = True  # Lock Interrupt
            buff = self.raw_touch()

            if self.int_handler is not None and buff is not None:
                x, y = self.normalize(*buff)
                self.int_handler(x, y)
            sleep(.1)  # Debounce falling edge
        elif pin.value() and self.int_locked:
            sleep(.1)  # Debounce rising edge
            self.int_locked = False  # Unlock interrupt

    def normalize(self, x, y):
        """Normalize mean X,Y values to match LCD screen."""
        x = self.width-int(self.x_multiplier * x + self.x_add)
        y = int(self.y_multiplier * y + self.y_add)
        return x, y

    def raw_touch(self):
        """Read raw X,Y touch values.

        Returns:
            tuple(int, int): X, Y
        """

        
        rr=self.touch_get()
        if rr is None:
             return None
        else:
            y,x=rr
        print('raw_touch2 rr=',y,x)
        # # x = 320 - int((rr[1]-430)*320/3270)
        # # y = int((rr[0]-430)*240/3270)
        # #x = 240 - int((rr[1]-430)*240/3270)
        # x = 320-int((rr[1]-430)*320/3270)
        # #y = int((rr[0]-430)*320/3270)
        # y = int((rr[0]-430)*240/3270)
        # print('raw_touch2 rr=',x,y)
                
        
        
        if self.x_min <= x <= self.x_max and self.y_min <= y <= self.y_max:
            return (x,y)
        else:
            return None


        
        
    def touch_get(self): 
        if self.int_pin.value() == 0:
            self.spi = SPI(1,2_500_000,sck=Pin(LCD_SCK),mosi=Pin(LCD_MOSI),miso=Pin(LCD_MISO))
            self.cs(0)
            X_Point = 0
            Y_Point = 0
            for i in range(0,5):
                 self.spi.write(bytearray([GET_X]))
                 Read_date = self.spi.read(2)
                 X_Point=X_Point+(((Read_date[0]<<8)+Read_date[1])>>3)
                
                 self.spi.write(bytearray([GET_Y]))
                 Read_date = self.spi.read(2)
                 Y_Point=Y_Point+(((Read_date[0]<<8)+Read_date[1])>>3)
                 time.sleep_us(20)

            X_Point=X_Point/5
            Y_Point=Y_Point/5

#   threshold: 400
#   transform:
#     mirror_x: true
#   calibration:
#     x_min: 280
#     x_max: 3860
#     y_min: 340
#     y_max: 3860

            
            self.cs(1) 
            self.spi = SPI(1,60_000_000,sck=Pin(LCD_SCK),mosi=Pin(LCD_MOSI),miso=Pin(LCD_MISO))
            Result_list = [X_Point,Y_Point]
            #print(Result_list)
            return(Result_list)        
