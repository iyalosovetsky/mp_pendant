# color_setup.py Customise for your hardware config

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2020 Peter Hinch



from machine import Pin, SPI

#from nanoguilib.ili9488_16 import ILI9488 as SSD
from nanoguilib.ili9488 import ILI9488 as SSD
LANDSCAPE = 0  # Default
REFLECT = 1
USD = 2
PORTRAIT = 4
import gc


SSD.COLOR_INVERT = 0

pdc = Pin(15, Pin.OUT, value=0)
pcs = Pin(13, Pin.OUT, value=1)
prst = None

gc.collect()  # Precaution before instantiating framebuf
spi = SPI(1, 60_000_000, sck=Pin(10), mosi=Pin(11), miso=Pin(12))
ssd = SSD(spi, height=480, width=320,  dc=pdc, cs=pcs, rst=prst)