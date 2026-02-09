#todo when send g0 x200 grbl set mpg=0 and so many bugs there
#https://github.com/gnea/grbl/blob/master/doc/markdown/commands.md
# 0x85 : Jog Cancel

# Immediately cancels the current jog state by a feed hold and automatically flushing any remaining jog commands in the buffer.
# Command is ignored, if not in a JOG state or if jog cancel is already invoked and in-process.
# Grbl will return to the IDLE state or the DOOR state, if the safety door was detected as ajar during the cancel.
# Feed Overrides

# Immediately alters the feed override value. An active feed motion is altered within tens of milliseconds.
# Does not alter rapid rates, which include G0, G28, and G30, or jog motions.
# Feed override value can not be 10% or greater than 200%.
# If feed override value does not change, the command is ignored.
# Feed override range and increments may be changed in config.h.
# The commands are:
# 0x90 : Set 100% of programmed rate.
# 0x91 : Increase 10%
# 0x92 : Decrease 10%
# 0x93 : Increase 1%
# 0x94 : Decrease 1%
# Rapid Overrides

# Immediately alters the rapid override value. An active rapid motion is altered within tens of milliseconds.
# Only effects rapid motions, which include G0, G28, and G30.
# If rapid override value does not change, the command is ignored.
# Rapid override set values may be changed in config.h.
# The commands are:
# 0x95 : Set to 100% full rapid rate.
# 0x96 : Set to 50% of rapid rate.
# 0x97 : Set to 25% of rapid rate.
# Spindle Speed Overrides

# Immediately alters the spindle speed override value. An active spindle speed is altered within tens of milliseconds.
# Override values may be changed at any time, regardless of if the spindle is enabled or disabled.
# Spindle override value can not be 10% or greater than 200%
# If spindle override value does not change, the command is ignored.
# Spindle override range and increments may be altered in config.h.
# The commands are:
# 0x99 : Set 100% of programmed spindle speed
# 0x9A : Increase 10%
# 0x9B : Decrease 10%
# 0x9C : Increase 1%
# 0x9D : Decrease 1%
# 0x9E : Toggle Spindle Stop

# Toggles spindle enable or disable state immediately, but only while in the HOLD state.
# The command is otherwise ignored, especially while in motion. This prevents accidental disabling during a job that can either destroy the part/machine or cause personal injury. Industrial machines handle the spindle stop override similarly.
# When motion restarts via cycle start, the last spindle state will be restored and wait 4.0 seconds (configurable) before resuming the tool path. This ensures the user doesn't forget to turn it back on.
# While disabled, spindle speed override values may still be altered and will be in effect once the spindle is re-enabled.
# If a safety door is opened, the DOOR state will supersede the spindle stop override, where it will manage the spindle re-energizing itself upon closing the door and resuming. The prior spindle stop override state is cleared and reset.
# 0xA0 : Toggle Flood Coolant

# Toggles flood coolant state and output pin until the next toggle or g-code command alters it.
# May be commanded at any time while in IDLE, RUN, or HOLD states. It is otherwise ignored.
# This override directly changes the coolant modal state in the g-code parser. Grbl will continue to operate normally like it received and executed an M8 or M9 g-code command.
# When $G g-code parser state is queried, the toggle override change will be reflected by an M8 enabled or disabled with an M9 or not appearing when M7 is present.
# 0xA1 : Toggle Mist Coolant

# Enabled by ENABLE_M7 compile-time option. Default is disabled.
# Toggles mist coolant state and output pin until the next toggle or g-code command alters it.
# May be commanded at any time while in IDLE, RUN, or HOLD states. It is otherwise ignored.
# This override directly changes the coolant modal state in the g-code parser. Grbl will continue to operate normally like it received and executed an M7 or M9 g-code command.
# When $G g-code parser state is queried, the toggle override change will be reflected by an M7 enabled or disabled with an M9 or not appearing when M8 is present.



LED_SCROLLLOCK =  0x04
LED_CAPSLOCK = 0x02
LED_NUMLOCK = 0x01
LED_ALL = LED_SCROLLLOCK + LED_CAPSLOCK + LED_NUMLOCK

BLINK_2 = 1
BLINK_5 = 2
BLINK_INFINITE = 3
NOBLINK = 4

 
DEBUG= False

 

 
 
KBD2GRBL ={
    'left':'-y',
    'right':'+y',
    'pageUp':'-z',
    'pageDown': '+z',
    'up':'+x', 
    'down':'-x', 
    # 'f1': '-stepXY',
    # '<': 'stepXY', 
    # '>': 'stepZ',
    # ';': 'feed',
    # 'f3': '-stepZ',
    # 'f5': '-feed',
    'esc': 'cancel',
    'reset': 'reset',
    '~':'~', #Cycle Start/Resume from Feed Hold, Door or Program pause.
    '!':'!', #Feed Hold – Stop all motion.
    'pause':'!', 
    'f1':'help', 
    'f2':'stepXY', 
    'f3':'stepZ', 
    'f4':'feed',
    'ctrl-left':'termLineLeft',
    'ctrl-right':'termLineRight',
    'ctrl-pageUp':'termLineUp',
    'ctrl-pageDown':'termLineDown',
    'ctrl-up':'histLineUp',
    'ctrl-down':'histLineDown',
    'ctrl-home':'termHome',
    
    '?':'?',
    '#':'#',
    'scrollLock':'#', # to toggle mpg MPG mode
    '^':'^',
    'f12':'^', # sends $X to grbl to unlock CNC from alarm mode
    '@':'@'

}



class SmartKbd(object):
    def __init__(self):
        self.cmd=bytearray(  [0x01,0x01,0xFE,0x02])
        
        self.grblCommand=''
        
        self.grblPrevCommand = ''

        self.grblMacro={}
        self.grblStateObj=  None
        
        

    def objGrblStateSetter(self,grblStateObj):
        self.grblStateObj = grblStateObj
        self.grblStateObj.gui.setEdit(self.grblCommand)

 
    @staticmethod
    def chars2Grbl(charIn:str): 
        return KBD2GRBL.get(charIn,charIn)
    
    def backspace(self):
        self.grblCommand =self.grblCommand[0:-1]
        self.grblStateObj.gui.setEdit(self.grblCommand)

    
    def put_char(self, char):
        self.grblCommand +=char
        self.grblStateObj.gui.setEdit(self.grblCommand)

    def space(self):
        self.put_char(' ')  
        self.grblStateObj.gui.setEdit(self.grblCommand)


    def clear(self):
        self.grblPrevCommand=self.grblCommand
        self.grblCommand = ''
        self.grblStateObj.gui.setEdit(self.grblCommand)  

    def set_macro(self, key:str):
        self.grblMacro[key]=self.grblCommand
        self.clear()

        
    def get_macro(self, key:str):
        self.clear()
        self.grblCommand=self.grblMacro.get(key,'')
        self.grblStateObj.gui.setEdit(self.grblCommand)
        return self.grblCommand
        
    def get(self):
        return self.grblCommand 

    def getc(self):
        self.clear()
        return self.grblPrevCommand
    
    @staticmethod
    def splitEsc(rxdata:str):
        l_chars=[]
        i=20
        l_chars=[]
        #https://learn.microsoft.com/ru-ru/windows/console/console-virtual-terminal-sequences
        while i>0 and len(rxdata)>0:
            i-=1
            if rxdata.startswith(chr(27)+"[D"):
                l_char = 'left'
                l_chars.append(l_char)
                rxdata=rxdata[3:]
            elif rxdata.startswith(chr(27)+"[C"):  
                l_char = 'right'
                l_chars.append(l_char)
                rxdata=rxdata[3:]
            elif rxdata.startswith(chr(27)+"[A"):  
                l_char = 'up'    
                l_chars.append(l_char)
                rxdata=rxdata[3:]
            elif rxdata.startswith(chr(27)+"[B"):  
                l_char = 'down'
                l_chars.append(l_char)        
                rxdata=rxdata[3:]
            elif rxdata.startswith(chr(27)+"[H"):  
                l_char = 'home'
                l_chars.append(l_char)        
                rxdata=rxdata[3:]
            elif rxdata.startswith(chr(27)+"[F"):  
                l_char = 'end'
                l_chars.append(l_char)        
                rxdata=rxdata[3:]
            elif rxdata.startswith(chr(27)+"[5~"):  
                l_char = 'pageUp'
                l_chars.append(l_char)        
                rxdata=rxdata[4:]
            elif rxdata.startswith(chr(27)+"[6~"):  
                l_char = 'pageDown'
                l_chars.append(l_char)        
                rxdata=rxdata[4:]
            elif rxdata.startswith(chr(27)+"[2~"):  
                l_char = 'insert'
                l_chars.append(l_char)        
                rxdata=rxdata[4:]
            elif rxdata.startswith(chr(27)+"[3~"):  
                l_char = 'delete'
                l_chars.append(l_char)        
                rxdata=rxdata[4:]
            elif rxdata.startswith(chr(27)+"OP"):  
                l_char = 'f1'
                l_chars.append(l_char)        
                rxdata=rxdata[3:]
            elif rxdata.startswith(chr(27)+"OQ"):  
                l_char = 'f2'
                l_chars.append(l_char)        
                rxdata=rxdata[3:]
            elif rxdata.startswith(chr(27)+"OR"):  
                l_char = 'f3'
                l_chars.append(l_char)        
                rxdata=rxdata[3:]
            elif rxdata.startswith(chr(27)+"OS"):  
                l_char = 'f4'
                l_chars.append(l_char)        
                rxdata=rxdata[3:]
            elif rxdata.startswith(chr(27)+"[15~"):  
                l_char = 'f5'
                l_chars.append(l_char)        
                rxdata=rxdata[5:]
            elif rxdata.startswith(chr(27)+"[17~"):  
                l_char = 'f6'
                l_chars.append(l_char)        
                rxdata=rxdata[5:]
            elif rxdata.startswith(chr(27)+"[18~"):  
                l_char = 'f7'
                l_chars.append(l_char)        
                rxdata=rxdata[5:]
            elif rxdata.startswith(chr(27)+"[19~"):  
                l_char = 'f8'
                l_chars.append(l_char)        
                rxdata=rxdata[5:]
            elif rxdata.startswith(chr(27)+"[20~"):  
                l_char = 'f9'
                l_chars.append(l_char)        
                rxdata=rxdata[5:]
            elif rxdata.startswith(chr(27)+"[21~"):  
                l_char = 'f10'
                l_chars.append(l_char)        
                rxdata=rxdata[5:]
            elif rxdata.startswith(chr(27)+"[23~"):  
                l_char = 'f11'
                l_chars.append(l_char)        
                rxdata=rxdata[5:]
            elif rxdata.startswith(chr(27)+"[24~"):  
                l_char = 'f12'
                l_chars.append(l_char)        
                rxdata=rxdata[5:]



            elif rxdata.startswith(chr(27)+"[1;5A"):  
                l_char = 'ctrl-up'    
                l_chars.append(l_char)
                rxdata=rxdata[6:]
            elif rxdata.startswith(chr(27)+"[1;5B"):  
                l_char = 'ctrl-down'
                l_chars.append(l_char)        
                rxdata=rxdata[6:]
            elif rxdata.startswith(chr(27)+"[1;5C"):
                l_char = 'ctrl-right'
                l_chars.append(l_char)
                rxdata=rxdata[6:]
            elif rxdata.startswith(chr(27)+"[1;5D"):  
                l_char = 'ctrl-left'
                l_chars.append(l_char)
                rxdata=rxdata[6:]
            elif rxdata.startswith(chr(27)+"[6;5~"):  
                l_char = 'ctrl-pageDown'
                l_chars.append(l_char)
                rxdata=rxdata[6:]
            elif rxdata.startswith(chr(27)+"[5;5~"):  
                l_char = 'ctrl-pageUp'
                l_chars.append(l_char)
                rxdata=rxdata[6:]
            elif rxdata.startswith(chr(27)+"[1;5H"):  
                l_char = 'ctrl-home'
                l_chars.append(l_char)
                rxdata=rxdata[6:]
            elif rxdata.startswith(chr(27)+"[1;5F"):  
                l_char = 'ctrl-end'
                l_chars.append(l_char)
                rxdata=rxdata[6:]
            elif rxdata.startswith(chr(27)+"[2;5~"):  
                l_char = 'ctrl-insert'
                l_chars.append(l_char)
                rxdata=rxdata[6:]
            elif rxdata.startswith(chr(27)+"[3;5~"):  
                l_char = 'ctrl-delete'
                l_chars.append(l_char)
                rxdata=rxdata[6:]
            elif rxdata.startswith(chr(27)+"[1;5P"):  
                l_char = 'ctrl-f1'
                l_chars.append(l_char)
                rxdata=rxdata[6:]
            elif rxdata.startswith(chr(27)+"[1;5Q"):  
                l_char = 'ctrl-f2'
                l_chars.append(l_char)
                rxdata=rxdata[6:]
            elif rxdata.startswith(chr(27)+"[1;5R"):  
                l_char = 'ctrl-f3'
                l_chars.append(l_char)
                rxdata=rxdata[6:]
            elif rxdata.startswith(chr(27)+"[1;5S"):  
                l_char = 'ctrl-f4'
                l_chars.append(l_char)
                rxdata=rxdata[6:]
            elif rxdata.startswith(chr(27)+"[15;5~"):  
                l_char = 'ctrl-f5'
                l_chars.append(l_char)
                rxdata=rxdata[7:]
            elif rxdata.startswith(chr(27)+"[17;5~"):  
                l_char = 'ctrl-f6'
                l_chars.append(l_char)
                rxdata=rxdata[7:]
            elif rxdata.startswith(chr(27)+"[18;5~"):  
                l_char = 'ctrl-f7'
                l_chars.append(l_char)
                rxdata=rxdata[7:]
            elif rxdata.startswith(chr(27)+"[19;5~"):  
                l_char = 'ctrl-f8'
                l_chars.append(l_char)
                rxdata=rxdata[7:]
            elif rxdata.startswith(chr(27)+"[20;5~"):  
                l_char = 'ctrl-f9'
                l_chars.append(l_char)
                rxdata=rxdata[7:]
            elif rxdata.startswith(chr(27)+"[21;5~"):  
                l_char = 'ctrl-f10'
                l_chars.append(l_char)
                rxdata=rxdata[7:]
            elif rxdata.startswith(chr(27)+"[23;5~"):  
                l_char = 'ctrl-f11'
                l_chars.append(l_char)
                rxdata=rxdata[7:]
            elif rxdata.startswith(chr(27)+"[24;5~"):  
                l_char = 'ctrl-f12'
                l_chars.append(l_char)
                rxdata=rxdata[7:]
            elif rxdata.startswith(chr(27)+chr(91)):
                l_char = 'ukn'
                l_chars.append(l_char)        
                rxdata=rxdata[3:]
            elif rxdata.startswith(chr(27)):
                l_char = 'esc'
                l_chars.append(l_char)                
                rxdata=rxdata[1:]
            elif rxdata.startswith(chr(18)):
                l_char = 'reset'
                l_chars.append(l_char)                
                rxdata=rxdata[1:]
            elif ord(rxdata[:1])==10:
                l_char ='enter'
                l_chars.append(l_char)                
                rxdata=rxdata[1:]
            elif ord(rxdata[:1])==8:
                l_char ='backspace'
                l_chars.append(l_char)                
                rxdata=rxdata[1:]
            elif ord(rxdata[:1])==9:
                l_char ='tab'
                l_chars.append(l_char)                
                rxdata=rxdata[1:]
            elif ord(rxdata[:1])==30:
                l_char ='pause'
                l_chars.append(l_char)                
                rxdata=rxdata[1:]                
            else:
                l_char =rxdata[:1]
                l_chars.append(l_char)                
                rxdata=rxdata[1:]
        return l_chars
    

    def proceedOneChar(self,charIn:str):
        
        if charIn =='enter' or (charIn is not None and len(charIn)>0 and  ord(charIn[-1:]) ==10  or ord(charIn[-1:]) ==13):
            self.grblStateObj.send2grbl(self.getc())
        elif charIn == ' ' or charIn == 'space' or charIn =='shift space' or charIn =='tab':
            self.put_char(' ')
            self.grblStateObj.neoShowEdit()
        elif charIn == 'backspace' or charIn =='shift backspace'  :
            self.backspace()
            self.grblStateObj.neoShowEdit()
        elif charIn in ('~','!','?','#','^','@') or \
                charIn =='left' or charIn =='right' or charIn =='pageUp' or charIn == 'pageDown' or \
                charIn =='up' or charIn =='down' or \
                charIn =='f1' or charIn =='f2' or charIn =='f3' or charIn =='f4' or \
                charIn =='f5' or charIn =='f6' or charIn =='f7' or charIn =='f8' or \
                charIn =='f9' or charIn =='f10' or charIn =='f11' or charIn =='f12' or \
                charIn =='ctrl-left' or charIn =='ctrl-right'  or charIn =='ctrl-pageDown' or charIn =='ctrl-pageUp'   or charIn =='ctrl-home' or \
                charIn =='esc' or charIn =='pause'  or charIn =='scrollLock' or charIn =='reset' : 
                self.grblStateObj.send2grbl(self.chars2Grbl(charIn))
                self.clear()
        elif charIn.startswith('ctrl-f') and len(charIn)>6:
            self.grblStateObj.send2grbl(self.get_macro(charIn[5:]))
            self.clear()
        elif charIn.startswith('alt-f') and len(charIn)>5:
            self.set_macro(charIn[4:])
            self.grblStateObj.neoShowEdit()
        elif charIn =='ctrl-up' or charIn == 'ctrl-down':
            hist=self.grblStateObj.getHist(diff=1 if charIn =='ctrl-down' else -1)
            if hist !='':
                self.clear()
                self.put_char(hist)
                self.grblStateObj.neoShowEdit()
        elif not(charIn.startswith('alt-') or charIn.startswith('shift-') or charIn.startswith('ctrl-') or charIn.startswith('opt-')
                    or charIn.startswith('ralt-') or charIn.startswith('rshift-') or charIn.startswith('rctrl-') or charIn.startswith('ropt-')):    
            self.put_char(charIn) 
            self.grblStateObj.neoShowEdit()



    def proceedChars(self,rxdata:str, DEBUG:bool = False  ): 
        #if DEBUG:
        #        print('proceedChars: rxdata=',rxdata)

        if self.grblStateObj is None:
            print('proceedChars: No grblStateObj FOUND!!!')
            return
        
        l_chars=self.splitEsc(rxdata)
        for l_char in (l_chars):
            #if DEBUG:
            #   print('proceedChars one: l_char=',l_char,ord(l_char))
            self.proceedOneChar(l_char)


#todo 
# hard beats every send ? or state changes        
# rapid commands
#1681920
#1681408


