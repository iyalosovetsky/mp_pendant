"""NS2009 Touch module."""
from time import sleep
from micropython import const  # type: ignore
import time
from machine import Pin,I2C


LCD_DC   = 15
LCD_CS   = 13
LCD_SCK  = 10
LCD_MOSI = 11
LCD_MISO = 12
LCD_BL   = 13
LCD_RST  = 15

TP_SDA    = 8
TP_SCL    = 9
TP_IRQ   = 14
SAMPLES = 10


#NS2009_LOW_POWER_READ_X = 0xc0
#NS2009_LOW_POWER_READ_Y = 0xd0
NS2009_LOW_POWER_READ_Y = 0xc0
NS2009_LOW_POWER_READ_X = 0xd0
NS2009_LOW_POWER_READ_Z1 = 0xe0
#SCREEN_X_PIXEL=320
#SCREEN_Y_PIXEL=480
SCREEN_X_PIXEL=480
SCREEN_Y_PIXEL=320

NS2009_ADDR =0x48 



class Touch(object):
    """Serial interface for XPT2046 Touch Screen Controller."""

 
    def __init__(self,  width=SCREEN_X_PIXEL, height=SCREEN_Y_PIXEL,
                 x_min=328, x_max=3865, y_min=334, y_max=3800):
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

        self.i2c = I2C(0, scl=Pin(TP_SCL), sda=Pin(TP_SDA), freq=400000)
        

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
            sample = self.ns2009_pos()  # get a touch
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
            buff = self.ns2009_pos()

            if self.int_handler is not None and buff is not None:
                x, y = self.normalize(*buff)
                self.int_handler(x, y)
            sleep(.1)  # Debounce falling edge
        elif pin.value() and self.int_locked:
            sleep(.1)  # Debounce rising edge
            self.int_locked = False  # Unlock interrupt

    def normalize(self, x, y):
        """Normalize mean X,Y values to match LCD screen."""
        x = int(self.x_multiplier * x + self.x_add)
        y = self.height-int(self.y_multiplier * y + self.y_add)
        return x, y



    def ns2009_recv(self, cmd):
       buf = bytearray(1)
       buf[0]=cmd
       self.i2c.writeto(NS2009_ADDR, buf)
       ret=self.i2c.readfrom(NS2009_ADDR, 2)   # read 2 bytes from device with address NS2009_ADDR
       return ret

    def ns2009_read(self, cmd):
       buf=self.ns2009_recv(cmd);
       return (buf[0] << 4) | (buf[1] >> 4)

    def ns2009_pos(self):
       press = self.ns2009_read(NS2009_LOW_POWER_READ_Z1)
       if (press > 30):
           x = self.ns2009_read(NS2009_LOW_POWER_READ_X)
           y = self.ns2009_read(NS2009_LOW_POWER_READ_Y)
           return x,y    
       else:
           return None
       



#def ns2009_recv(cmd):
#   buf = bytearray(1)
#   buf[0]=cmd
#   i2c.writeto(NS2009_ADDR, buf)
#   ret=i2c.readfrom(NS2009_ADDR, 2)   # read 2 bytes from device with address NS2009_ADDR
#   return ret           
           
#def ns2009_read( cmd):
#       buf=ns2009_recv(cmd);
#       return (buf[0] << 4) | (buf[1] >> 4)       
       

  
        

