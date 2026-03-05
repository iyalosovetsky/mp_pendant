# ILI9488 nano-gui driver for ili9488 displays

### Based on ili9486.py by Peter Hinch.
### Retaining his copyright

# Copyright (c) Peter Hinch 2022-2025
# Released under the MIT license see LICENSE

# This driver, adapted from ILI9486, was contributed by Carl Pottle (cpottle9).

# Note: If your hardware uses the ILI9488 parallel interface
# you will likely be better off using the ili9486 driver.
# It will send 2 bytes per pixel which will run faster.
#
# You must use this driver only when using the ILI9488 SPI
# interface. It will send 3 bytes per pixel.

# ILI9488 max SPI baudrate 20MHz (datasheet 17.4.3) but 24MHz is a reasonable overclock.

from time import sleep_ms
import gc 
import framebuf
import asyncio
from nanoguilib.boolpalette import BoolPalette

# Do processing from end to beginning for
# small performance improvement.
# greyscale
@micropython.viper
def _lcopy_gs(dest: ptr8, source: ptr8, length: int):
     # rgb565 - 16bit/pixel
    n = 0
    for x in range(length):
        c = source[x]
        dest[n] = c >> 4  # current pixel
        n += 1
        dest[n] = c & 0x0f  # next pixel
        n += 1


# Do processing from end to beginning for
# small performance improvement.
# color
@micropython.viper
def _lcopy(dest:ptr16, source:ptr8, lut:ptr16, length:int):
    # rgb565 - 16bit/pixel
    n = 0
    for x in range(length):
        c = source[x]
        dest[n] = lut[c >> 4]  # current pixel
        n += 1
        dest[n] = lut[c & 0x0f]  # next pixel
        n += 1

def _lcopy_blank(dest:ptr16,  length:int):
    # rgb565 - 16bit/pixel
    n = 0
    for x in range(length):
        dest[n] = 0  # current pixel
        n += 1
        dest[n] = 0  # next pixel
        n += 1
 
class ILI9488(framebuf.FrameBuffer):

    lut = bytearray(32)
    #lut = bytearray(0xFF for _ in range(32))  # set all colors to BLACK
    COLOR_INVERT = 0

    """Serial interface for 16-bit color (5-6-5 RGB) ILI9488 display.
    Note:  All coordinates are zero based.
    """

    # Command constants from ILI9488 datasheet
    NOP = const(0x00)  # No-op
    SWRESET = const(0x01)  # Software reset
    RDDID = const(0x04)  # Read display ID info
    RDDST = const(0x09)  # Read display status
    SLPIN = const(0x10)  # Enter sleep mode
    SLPOUT = const(0x11)  # Exit sleep mode
    PTLON = const(0x12)  # Partial mode on
    NORON = const(0x13)  # Normal display mode on
    RDMODE = const(0x0A)  # Read display power mode
    RDMADCTL = const(0x0B)  # Read display MADCTL
    RDPIXFMT = const(0x0C)  # Read display pixel format
    RDIMGFMT = const(0x0D)  # Read display image format
    RDSELFDIAG = const(0x0F)  # Read display self-diagnostic
    INVOFF = const(0x20)  # Display inversion off
    INVON = const(0x21)  # Display inversion on
    GAMMASET = const(0x26)  # Gamma set
    DISPLAY_OFF = const(0x28)  # Display off
    DISPLAY_ON = const(0x29)  # Display on
    SET_COLUMN = const(0x2A)  # Column address set
    SET_PAGE = const(0x2B)  # Page address set
    WRITE_RAM = const(0x2C)  # Memory write
    READ_RAM = const(0x2E)  # Memory read
    PTLAR = const(0x30)  # Partial area
    VSCRDEF = const(0x33)  # Vertical scrolling definition
    MADCTL = const(0x36)  # Memory access control
    VSCRSADD = const(0x37)  # Vertical scrolling start address
    PIXFMT = const(0x3A)  # COLMOD: Pixel format set
    WRITE_DISPLAY_BRIGHTNESS = const(0x51)  # Brightness hardware dependent!
    READ_DISPLAY_BRIGHTNESS = const(0x52)
    WRITE_CTRL_DISPLAY = const(0x53)
    READ_CTRL_DISPLAY = const(0x54)
    WRITE_CABC = const(0x55)  # Write Content Adaptive Brightness Control
    READ_CABC = const(0x56)  # Read Content Adaptive Brightness Control
    WRITE_CABC_MINIMUM = const(0x5E)  # Write CABC Minimum Brightness
    READ_CABC_MINIMUM = const(0x5F)  # Read CABC Minimum Brightness
    FRMCTR1 = const(0xB1)  # Frame rate control (In normal mode/full colors)
    FRMCTR2 = const(0xB2)  # Frame rate control (In idle mode/8 colors)
    FRMCTR3 = const(0xB3)  # Frame rate control (In partial mode/full colors)
    INVCTR = const(0xB4)  # Display inversion control
    DFUNCTR = const(0xB6)  # Display function control
    PWCTR1 = const(0xC0)  # Power control 1
    PWCTR2 = const(0xC1)  # Power control 2
    PWCTRA = const(0xCB)  # Power control A
    PWCTRB = const(0xCF)  # Power control B
    VMCTR1 = const(0xC5)  # VCOM control 1
    VMCTR2 = const(0xC7)  # VCOM control 2
    RDID1 = const(0xDA)  # Read ID 1
    RDID2 = const(0xDB)  # Read ID 2
    RDID3 = const(0xDC)  # Read ID 3
    RDID4 = const(0xDD)  # Read ID 4
    GMCTRP1 = const(0xE0)  # Positive gamma correction
    GMCTRN1 = const(0xE1)  # Negative gamma correction
    DTCA = const(0xE8)  # Driver timing control A
    DTCB = const(0xEA)  # Driver timing control B
    POSC = const(0xED)  # Power on sequence control
    ENABLE3G = const(0xF2)  # Enable 3 gamma control
    PUMPRC = const(0xF7)  # Pump ratio control


    ROTATE = {
        0: 0x88, #width < height,  portrait
        90: 0xE8,  #width > height, landscape, usd
        180: 0x48, #width < height,  portrait, usd
        270: 0x28, #width > height, landscape 
    }


    # Convert r, g, b in range 0-255 to a 16 bit colour value
    # 5-6-5 format
    #  byte order not swapped (compared to ili9486 driver).
    #@classmethod
    #def rgb(cls, r, g, b):
    #    return cls.COLOR_INVERT ^ ((r & 0xF8) << 8 | (g & 0xFC) << 3 | (b >> 3))
    # Convert r, g, b in range 0-255 to a 16 bit colour value rgb565.
    # LS byte goes into LUT offset 0, MS byte into offset 1
    # Same mapping in linebuf so LS byte is shifted out 1st
    ## For some reason color must be inverted on this controller.
    @classmethod
    def rgb(cls,r, g, b):
        #return ((b & 0xf8) << 5 | (g & 0x1c) << 11 | (g & 0xe0) >> 5 | (r & 0xf8)) ^ 0xffff    
        return ((b & 0xf8) << 5 | (g & 0x1c) << 11 | (g & 0xe0) >> 5 | (r & 0xf8)) 

    # Transpose width & height for landscape mode
    def __init__(
        self,
        spi,
        cs,
        dc,
        rst,
        height=320,
        width=480,
        usd=False,
        mirror=False,
        init_spi=False,
        lines_per_write=4,
    ):
        self._spi = spi
        self._cs = cs
        self._dc = dc
        self._rst = rst
        self.lock_mode = False  # If set, user lock is passed to .do_refresh
        self.height = height  # Logical dimensions for GUIs
        self.width = width
        self._spi_init = init_spi
        self._gscale = False  # Interpret buffer as index into color LUT
        #self._gscale = True  # Interpret buffer as index into color LUT
        self.mode = framebuf.GS4_HMSB
        self.palette = BoolPalette(self.mode)
        self._blank = False
        if self.width > self.height:
            # landscape
            self.rotation =self.ROTATE[90] if usd else self.ROTATE[270] # 0xE8 if usd else 0x28
        else:
            # portrait
            self.rotation = self.ROTATE[180] if usd else self.ROTATE[0] # 0x48 if usd else 0x88
        if mirror:
            self.rotation ^= 0x80  # toggle MY    

        

        
        #
        # lines_per_write must divide evenly into height
        #
        if (self.height % lines_per_write) != 0:
            raise ValueError("lines_per_write invalid")
        #self._lines_per_write = lines_per_write
        self._lines_per_write = 1
        gc.collect()
        buf = bytearray(height * width // 2)
        self.mvb = memoryview(buf)
        super().__init__(buf, width, height, self.mode)  # Logical aspect ratio
        #self._linebuf = bytearray(self._lines_per_write * self.width * 3)
        self._linebuf = bytearray(self._lines_per_write *self.width * 2)  # 16 bit color out
        




        # Hardware reset
        if self._rst is not None:
            self._rst(0)
            sleep_ms(50)
            self._rst(1)
        sleep_ms(50)
        if self._spi_init:  # A callback was passed
            self._spi_init(spi)  # Bus may be shared
        self._lock = asyncio.Lock()
        # Send initialization commands

        # self._wcmd(b"\x01")  # SWRESET Software reset
        # sleep_ms(100)
        # self._wcmd(b"\x11")  # sleep out
        # sleep_ms(20)
        # self._wcd(b"\x3a", b"\x66")  # interface pixel format 18 bits per pixel


        self._wcmd(int.to_bytes(self.SWRESET))  # SWRESET Software reset
        sleep_ms(100)
        self._wcmd(int.to_bytes(self.SLPOUT))  # sleep out
        sleep_ms(20)
        #self.write_cmd(self.PIXFMT, 0x66)  # interface pixel format 18 bits per pixel
        self.write_cmd(self.PIXFMT, 0x55)  # interface pixel format 18 bits per pixel
        self.write_cmd(self.WRITE_DISPLAY_BRIGHTNESS, 0x07 )
        self.write_cmd(self.WRITE_CTRL_DISPLAY, 0x2c )
        self.write_cmd(self.WRITE_DISPLAY_BRIGHTNESS, 0x77 )
        self.write_cmd(self.WRITE_CABC_MINIMUM, 0x80 )


        self.write_cmd(self.PWCTRB, 0x00, 0xC1, 0x30)  # Pwr ctrl B
        self.write_cmd(self.POSC, 0x64, 0x03, 0x12, 0x81)  # Pwr on seq. ctrl
        self.write_cmd(self.DTCA, 0x85, 0x00, 0x78)  # Driver timing ctrl A
        self.write_cmd(self.PWCTRA, 0x39, 0x2C, 0x00, 0x34, 0x02)  # Pwr ctrl A
        self.write_cmd(self.PUMPRC, 0x20)  # Pump ratio control
        self.write_cmd(self.DTCB, 0x00, 0x00)  # Driver timing ctrl B
        self.write_cmd(self.PWCTR1, 0x23)  # Pwr ctrl 1
        self.write_cmd(self.PWCTR2, 0x10)  # Pwr ctrl 2
        self.write_cmd(self.VMCTR1, 0x3E, 0x28)  # VCOM ctrl 1
        self.write_cmd(self.VMCTR2, 0x86)  # VCOM ctrl 2
        #+self.write_cmd(self.MADCTL, self.rotation)  # Memory access ctrl
        self.write_cmd(self.VSCRSADD, 0x00)  # Vertical scrolling start address
        #+self.write_cmd(self.PIXFMT, 0x55)  # COLMOD: Pixel format
        self.write_cmd(self.FRMCTR1, 0x00, 0x18)  # Frame rate ctrl
        self.write_cmd(self.DFUNCTR, 0x02,0x02)
        self.write_cmd(self.ENABLE3G, 0x00)  # Enable 3 gamma ctrl
        self.write_cmd(self.GAMMASET, 0x01)  # Gamma curve selected
        self.write_cmd(self.GMCTRP1, 0x0F, 0x31, 0x2B, 0x0C, 0x0E, 0x08, 0x4E,
                       0xF1, 0x37, 0x07, 0x10, 0x03, 0x0E, 0x09, 0x00)
        self.write_cmd(self.GMCTRN1, 0x00, 0x0E, 0x14, 0x03, 0x11, 0x07, 0x31,
                       0xC1, 0x48, 0x08, 0x0F, 0x0C, 0x31, 0x36, 0x0F)


        self._wcd(int.to_bytes(self.SET_COLUMN), int.to_bytes(self.width - 1, 4, "big"))
        self._wcd(int.to_bytes(self.SET_PAGE), int.to_bytes(self.height - 1, 4, "big"))  # SET_PAGE ht





        # if self.width > self.height:
        #     # landscape
        #     madctl = 0xE8 if usd else 0x28
        # else:
        #     # portrait
        #     madctl = 0x48 if usd else 0x88
        # if mirror:
        #     madctl ^= 0x80  # toggle MY
        #memory accect control 0x80 portrait 0x20 landscape 90 0x40 portrait usd 0xE0 landscape usd   
        # self._wcd(b"\x36", madctl.to_bytes(1, "big"))  # MADCTL: RGB portrait mode
        # self._wcmd(b"\x11")  # sleep out
        # self._wcmd(b"\x29")  # display on
        self._wcd(int.to_bytes(self.MADCTL), self.rotation.to_bytes(1, "big"))  # MADCTL: RGB portrait mode
        self._wcmd(int.to_bytes(self.SLPOUT))  # sleep out
        self._wcmd(int.to_bytes(self.DISPLAY_ON))  # display on

        # self.write_cmd(self.PWCTRB, 0x00, 0xC1, 0x30)  # Pwr ctrl B
        # self.write_cmd(self.POSC, 0x64, 0x03, 0x12, 0x81)  # Pwr on seq. ctrl
        # self.write_cmd(self.DTCA, 0x85, 0x00, 0x78)  # Driver timing ctrl A
        # self.write_cmd(self.PWCTRA, 0x39, 0x2C, 0x00, 0x34, 0x02)  # Pwr ctrl A
        # self.write_cmd(self.PUMPRC, 0x20)  # Pump ratio control
        # self.write_cmd(self.DTCB, 0x00, 0x00)  # Driver timing ctrl B
        # self.write_cmd(self.PWCTR1, 0x23)  # Pwr ctrl 1
        # self.write_cmd(self.PWCTR2, 0x10)  # Pwr ctrl 2
        # self.write_cmd(self.VMCTR1, 0x3E, 0x28)  # VCOM ctrl 1
        # self.write_cmd(self.VMCTR2, 0x86)  # VCOM ctrl 2
        #+self.write_cmd(self.MADCTL, self.rotation)  # Memory access ctrl
        # self.write_cmd(self.VSCRSADD, 0x00)  # Vertical scrolling start address
        # #+self.write_cmd(self.PIXFMT, 0x55)  # COLMOD: Pixel format
        # self.write_cmd(self.FRMCTR1, 0x00, 0x18)  # Frame rate ctrl
        # self.write_cmd(self.DFUNCTR, 0x02,0x02)
        # self.write_cmd(self.ENABLE3G, 0x00)  # Enable 3 gamma ctrl
        # self.write_cmd(self.GAMMASET, 0x01)  # Gamma curve selected
        # self.write_cmd(self.GMCTRP1, 0x0F, 0x31, 0x2B, 0x0C, 0x0E, 0x08, 0x4E,
        #                0xF1, 0x37, 0x07, 0x10, 0x03, 0x0E, 0x09, 0x00)
        # self.write_cmd(self.GMCTRN1, 0x00, 0x0E, 0x14, 0x03, 0x11, 0x07, 0x31,
        #                0xC1, 0x48, 0x08, 0x0F, 0x0C, 0x31, 0x36, 0x0F)
        # self.write_cmd(self.SLPOUT)  # Exit sleep
        # sleep(.1)
        # self.write_cmd(self.DISPLAY_ON)  # Display on
        # sleep(.1)
        # self.clear()


    def display_blank(self, blank):
        """Turn display off."""
        self._blank = blank

    def display_off(self):
        """Turn display off."""
        self._wcmd(int.to_bytes(self.DISPLAY_OFF)) # display off

    def display_on(self):
        """Turn display on."""
        self._wcmd(int.to_bytes(self.DISPLAY_ON))  # display on

    def clear(self, color=0):
        """Clear display.
        Args:
            color (Optional int): RGB565 color value (Default: 0 = Black).
        """
        w = self.width
        h = self.height
        # Clear display in 1024 byte blocks
        if color:
            line = color.to_bytes(2, 'big') * (w * 8)
        else:
            line = bytearray(w * 16)
        for y in range(0, h, 8):
            self.block(0, y, w - 1, y + 7, line)

    def cleanup(self):
        """Clean up resources."""
        self.clear()
        self.display_off()
        self.spi.deinit()
        print('display off')

    def sleep(self, enable=True):
        """Enters or exits sleep mode.
        Args:
            enable (bool): True (default)=Enter sleep mode, False=Exit sleep
        """
        if enable:
            self._wcmd(int.to_bytes(self.SLPIN))
        else:
            self._wcmd(int.to_bytes(self.SLPOUT))        


    def greyscale(self, gs=None):
        if gs is not None:
            self._gscale = gs
        return self._gscale

    # @micropython.native  # Made almost no difference to timing
    def show(self):  # Physical display is in portrait mode
        lb = self._linebuf
        buf = self.mvb
        cm = self._gscale  # color False, greyscale True
        if self._spi_init:  # A callback was passed
            self._spi_init(self._spi)  # Bus may be shared
        #self._wcmd(b"\x2c")  # WRITE_RAM
        self._wcmd(int.to_bytes(self.WRITE_RAM))  # WRITE_RAM
        
        self._dc(1)
        self._cs(0)
        wd = self.width >> 1
        end = self.height * wd
        #ht = self.height
        spi_write = self._spi.write
        length = self._lines_per_write * wd
        #r = range(0, wd * ht, length)
        r= range(0, end, wd)
        if self._blank :
            lcopy = _lcopy_blank  # Copy and map colors
            for start in r:  # For each line
                lcopy(lb, length)
                spi_write(lb)      
        elif cm:
            lcopy = _lcopy_gs  # Copy greyscale
            for start in r:  # For each line
                lcopy(lb, buf[start:], length)
                spi_write(lb)
        else:
            clut = ILI9488.lut
            lcopy = _lcopy  # Copy and map colors
            for start in r:  # For each line
                lcopy(lb, buf[start:], clut, length)
                spi_write(lb)

        self._cs(1)

    def short_lock(self, v=None):
        if v is not None:
            self.lock_mode = v  # If set, user lock is passed to .do_refresh
        return self.lock_mode

    # nanogui apps typically call with no args. ugui and tgui pass split and
    # may pass a Lock depending on lock_mode
    async def do_refresh(self, split=4, elock=None):
        if elock is None:
            elock = asyncio.Lock()
        async with self._lock:
            lines, mod = divmod(self.height, split)  # Lines per segment
            if mod:
                raise ValueError("Invalid do_refresh arg 'split'")
            if lines % self._lines_per_write != 0:
                raise ValueError(
                    "Invalid do_refresh arg 'split' for lines_per_write of %d"
                    % (self._lines_per_write)
                )
            clut = ILI9488.lut
            lb = self._linebuf
            buf = self.mvb
            cm = self._gscale  # color False, greyscale True
            #self._wcmd(b"\x2c")  # WRITE_RAM
            self._wcmd(int.to_bytes(self.WRITE_RAM))  # WRITE_RAM
            self._dc(1)
            wd = self.width // 2
            line = 0
            spi_write = self._spi.write
            length = self._lines_per_write * wd
            for _ in range(split):  # For each segment
                async with elock:
                    if self._spi_init:  # A callback was passed
                        self._spi_init(self._spi)  # Bus may be shared
                    self._cs(0)
                    r = range(wd * line, wd * (line + lines), length)
                    if cm:
                        lcopy = _lcopy_gs  # Copy and greyscale
                        for start in r:
                            lcopy(lb, buf[start:], length)
                            spi_write(lb)
                    else:
                        lcopy = _lcopy  # Copy and map colors
                        for start in r:
                            lcopy(lb, buf[start:], clut, length)
                            spi_write(lb)

                    line += lines
                    self._cs(1)  # Allow other tasks to use bus
                await asyncio.sleep_ms(0)






    # Write a command.
    def _wcmd(self, command):
        self._dc(0)
        self._cs(0)
        self._spi.write(command)
        self._cs(1)




    def write_data(self, data):
        """Write data to OLED (MicroPython).
        Args:
            data (bytes): Data to transmit.
        """
        self._dc(1)
        self._cs(0)
        self._spi.write(data)
        self._cs(1)

    def write_cmd(self, command, *args):
        """Write command to OLED (MicroPython).
        Args:
            command (byte): ILI9488 command code.
            *args (optional bytes): Data to transmit.
        """
        self._dc(0)
        self._cs(0)
        self._spi.write(bytearray([command]))
        self._cs(1)
        # Handle any passed data
        if len(args) > 0:
            self.write_data(bytearray(args))



    # Write a command followed by a data arg.
    def _wcd(self, command, data):
        self._dc(0)
        self._cs(0)
        self._spi.write(command)
        self._cs(1)
        self._dc(1)
        self._cs(0)
        self._spi.write(data)
        self._cs(1)

#
# command 0x01 #Software Reset 
# delay 100
# command 0x11 #Sleep out
# delay 20

# command 0x20 #Display Inversion OFF
# delay 20

# #command 0x28 #Display OFF
# command 0xE0 0x00 0x03 0x09 0x08 0x16 0x0A 0x3F 0x78 0x4C 0x09 0x0A 0x08 0x16 0x1A 0x0F #Positive Gamma Control
# command 0xE1 0x00 0x16 0x19 0x03 0x0F 0x05 0x32 0x45 0x46 0x04 0x0E 0x0D 0x35 0x37 0x0F #Negative Gamma Control
# command 0xC0 0x17 0x15 #Power Control 1
# command 0xC1 0x41 #Power Control 2
# #command 0xC5 0x00 0x4D 0x80 #VCOM Control 1 need 4 parameters
# #command 0x36 0xE8			#Memory Access Control # BGR (0x0x = portrait 0° mirror, 0x8x = portrait 180°, 0x2x = landscape 90°, 0x4x = portrait 0°)
# command 0x36 0xE0 #Memory Access Control # BGR (0x0x = portrait 0° mirror, 0x8x = portrait 180°, 0x2x = landscape 90°, 0x4x = portrait 0°)
# #command 0x3A 0x66 #INTERFACE_PIXEL_FORMAT #0x66 - 18 bit colour for SPI, 0x55 16 bit colour for parallel
# command 0x3A 0x2D #INTERFACE_PIXEL_FORMAT #0x36 0x66 - 18 bit colour for SPI,0x2d  0x55 16 bit colour for parallel
# command 0xB0 0x80			#Interface Mode Control 219 page. 0x80 - SDO (MOSI) pin not used.
# #command 0xB0 0x00 #Interface Mode Control
# #command 0xB1 0xA0 #Frame Rate Control
# command 0xB1 0xB0 0x11 #Frame Rate Control
# command 0xB4 0x01  #1dot inversion


# command 0xB6 0x02 0x02 0x3B #Display Inversion Control  - right Display Function Control 
# #command 0xB7 0x86			# Entry Mode Set p.233
# command 0xB7 0xC6 # Entry Mode Set p.233
# #command 0xE9 0x00			#Set Image Function

# command 0xF7 0xA9 0x51 0x2C 0x82 #Adjust Control 3 - defaults
# #command 0x21 inversion on 
# command 0x11 #Sleep out
# delay 200
# command 0x29 #Display On
                
