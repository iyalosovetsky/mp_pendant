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

X_ARROW_COLOR = 'red'
Y_ARROW_COLOR = 'green'
Z_ARROW_COLOR = 'blue'

DEBUG= False

VFD_PURPLE = 0x00FFD2
VFD_GREEN = 0x30BF30
VFD_RED = 0xCF3030
VFD_BLUE = 0x4040CF
VFD_YELLOW = 0xFFFF00
VFD_YELLOW2 = 0xBFBF00
VFD_WHITE = 0xCFCFCF

VFD_ARROW_X = VFD_RED
VFD_ARROW_Y = VFD_GREEN
VFD_ARROW_Z = VFD_BLUE
VFD_BG = 0x000505

GRBL_QUERY_INTERVAL = 0.5

C_STEP_MAX = 100.0
C_STEP_MIN = 0.1

C_STEP_Z_MAX = 20.0
C_STEP_Z_MIN = 0.1

C_FEED_MAX = 2000.0
C_FEED_MIN = 200.0

DXYZ_STEPS=[0.1,1.,10.,50.]
FEED_STEPS=[10.,100.,200.,500.,1000.]



import   time
from adafruit_display_text import label
import terminalio
import microcontroller

class GrblState(object):
    def __init__(self,kbd,uart_grbl_mpg,neo,
                  state:str = '', 
                  mpg:bool = None,
                  mX:float = 0.0,
                  mY:float = 0.0,
                  mZ:float = 0.0,
                  mA:float = 0.0,
                  mB:float = 0.0,
                  mC:float = 0.0,
                  wX:float = 0.0,
                  wY:float = 0.0,
                  wZ:float = 0.0,
                  dXY:float = DXYZ_STEPS[1],
                  dZ:float = DXYZ_STEPS[1],
                  feedrate =  FEED_STEPS[2]
                  ) :
        self.__version__ = '0.1'
        self._state = state
        self._state_prev = ''
        self._error = ''
        self._alarm = ''
        self.query_now(3)
        self._query4MPG_countDown = 2
        self.time2query = time.monotonic()
        self._mpg = mpg
        self._mpg_prev = ''
        self._mX = mX
        self._mY = mY
        self._mZ = mZ
        self._mA = mA
        self._mB = mB
        self._mC = mC
        
        self._wX = wX
        self._wY = wY
        self._wZ = wZ
        self._dXY = dXY
        self._dZ = dZ
        self._feedrate = feedrate
        self._state_is_changed = False
        self.grbl_state = '' # text in chevron
        self.grbl_info = '' # text in bracket
        self._execProgress = 'ok'
        self.kbd = kbd
        self.uart_grbl_mpg = uart_grbl_mpg
        self.neo = neo
        self._jog_arrow = ''
        self.idleCounter = 0
        self.editCmd = ''
        self.statetext = ''
        self._state_code='init'
        self.prev_statetext  = ''
        self.grblCmd2send=[]
        self.grblCmdHist=[]
        self.grblCmd2HistPos = 0
        self.term_line_from=1
        self.term_pos_from=0
        self._state_time_change = time.monotonic()
        self._msg_conf = [
            ('x', '     ', VFD_GREEN, 190, 15, 3),
            ('y', '     ', VFD_RED, 190, 55, 3),
            ('z', '     ', VFD_BLUE, 190, 95, 3),
            ('cmd', '     ', VFD_WHITE, 0, 170, 2),
            ('state', '     ', VFD_WHITE, 190, 130, 2),
            ('term', '\nF1\nHelp', VFD_WHITE,10, 20, 2),
            ('icon', 'grbl', VFD_PURPLE, 20, 20, 4),
            ('info', '    ', VFD_WHITE, 0, 200, 1)
        ]
        self.labels = {}  # dictionary of configured messages_labels
        self.help = [
           'ctrl-r\nreboot',
           'ctrl-c\ncancel',
           '#\nMPG',
           '^\nunlock',
           'esc\ncancel',
           'f2\nDxy',
           'f3\nDz',
           'f4\nfeed',
           'ctrl-\nup\nhistory',
           'ctrl-\ndown\nhistory',
           'ctrl-\nPgUp\nscreen',
           'ctrl-\nPgDown\nscreen',
           'ctrl-\nleft\nscreen',
           'ctrl-\nright\nscreen',
           'ctrl-\nhome\nscreen',


           '~\nstart\\ \nresume',
           '!\nfeed\\ \nhold',
           '?\nquery'
        ]     
        self.helpIdx=-1



        for c1 in self._msg_conf:
            (name, textline, color, x, y, scale) = c1  # unpack tuple into five var names
            l_label = label.Label(terminalio.FONT, text=textline, color=color, scale=scale)
            l_label.x = x
            l_label.y = y
            self.labels[name] = l_label
            self.neo.display.root_group.append(l_label)


        self.hello()
        

    def decTermLinePos(self):
       if len(self.grbl_info)>0 and self.term_line_from>3:
          self.term_line_from -= 3

    def decTermPos(self):
       if len(self.grbl_info)>0 and self.term_pos_from>4:
          self.term_pos_from -= 5



    def incTermLinePos(self):
        if len(self.grbl_info)>0:
          lines = self.grbl_info.count('\n')  
          lines += 1
          if self.term_line_from<lines:
             self.term_line_from += 3

    def incTermPos(self):
        if len(self.grbl_info)>0:
          if self.term_pos_from<50:
             self.term_pos_from += 5

    def homeTermPos(self):
        if len(self.grbl_info)>0:
           self.term_pos_from = 0
           self.term_line_from = 1


    def neoSplitTerm(self,text):
      textF=''
      ii=0
      jj=0
      for cc in text.split('\n'):
         jj+=1
         if jj<self.term_line_from:
            continue
            
         ii+=1
         if ii>5:
            break
         if len(textF)>100:
             break
         if ii>1:
            textF +='\n'
         textF +=cc.replace('[ALARMCODE:','').replace('[SETTING:','')[self.term_pos_from:25+self.term_pos_from]
      return textF 
    
    
    def neoSplitLine(self,text):
      textF=''
      len1 =0
      for cc in text.split('|'):
        if cc.startswith('Bf'):
            continue
        if cc.startswith('MPos'):
            continue
        if cc.startswith('WCO:0.000,0.000,0.000'):
            continue
        if cc.startswith('Ov:100,100,100'):
            continue
        if cc.startswith('FW:grblHAL'):
            continue
        if textF=='':
            textF +=cc
            len1 += len(cc)
            continue            
        else:
            if len1+len(cc)>50:
                textF +='\n'
                len1 =0
            len1 += len(cc)+1
            textF +='|'+cc
      return textF
            
        
          

    def neoLabel(self,text,id='info',color=None):
        if color is not None and isinstance(color,str):
           if color.lower() == 'red':
              color = VFD_RED
           elif color.lower() == 'green':   
              color = VFD_GREEN
           elif color.lower() == 'blue':   
              color = VFD_BLUE
           elif color.lower() == 'purple':   
              color = VFD_PURPLE      
           elif color.lower() == 'yellow':   
              color = VFD_YELLOW      
           elif color.lower() == 'white':   
              color = VFD_WHITE      

        if id=='x':
          self.labels[id].text = '{0:.1f}'.format(self._mX)
          self.labels[id].color=VFD_ARROW_X
        elif id=='y':
          self.labels[id].text = '{0:.1f}'.format(self._mY)  
          self.labels[id].color=VFD_ARROW_Y
        elif id=='z':
          self.labels[id].text = '{0:.1f}'.format(self._mZ)  
          self.labels[id].color=VFD_ARROW_Z
        elif id=='cmd':
          self.labels[id].text = text
          if color is None:
             self.labels[id].color=VFD_YELLOW2
        elif id=='state':
          self.labels[id].text = text
          if color is None and text.lower().startswith('alarm'):
             self.labels[id].color=VFD_RED
          elif color is None and (text.lower().startswith('run') or text.lower().startswith('jog')):
             self.labels[id].color=VFD_WHITE
          elif color is None:
             self.labels[id].color=VFD_GREEN
          else:   
             self.labels[id].color=color
        elif id=='icon':
          self.labels['term'].hidden=(len(text.strip())>2)
          self.labels[id].text = text
          if color is None:
             self.labels[id].color=VFD_GREEN
          else:   
             self.labels[id].color=color

        elif id=='term':
        #   self.labels['term'].hidden= False
          self.labels[id].text = self.neoSplitTerm(text)
          if color is None:
             self.labels[id].color=VFD_GREEN
          else:   
             self.labels[id].color=color
        elif id=='info':
          self.labels[id].text = self.neoSplitLine(text)
          if color is None:
             self.labels[id].color=VFD_PURPLE if self._mpg  else VFD_WHITE
          else:   
             self.labels[id].color=color

             
    def hello(self):
       self.neoLabel('GrblHAL v'+self.__version__,id='cmd',color=VFD_YELLOW)
       time.sleep(0.5)

    def getHelp(self):
       self.helpIdx+=1
       self.helpIdx=self.helpIdx%len(self.help)
       return self.help[self.helpIdx]
       

    def neoIcon(self,text,color=None) :     
        self.neoLabel(text,id='icon',color=VFD_YELLOW if color is None else  color)

    def neoTerm(self,text,color=None) :   
        #print("neoTerm",text)  
        self.neoLabel(text,id='term',color=VFD_WHITE if color is None else  color)
       
    def inc_feedrate(self):
      if self._feedrate+100.0 > C_FEED_MAX:
           self._feedrate = C_FEED_MAX
      else:    
           self._feedrate +=100.0
      self._state_prev='feed'
      #print('g_feedrate now',self._feedrate)  


    def dec_feedrate(self):
      if self._feedrate-100.0 < C_FEED_MIN:
           self._feedrate = C_FEED_MIN
      else:    
           self._feedrate -=100.0
      self._state_prev='feed'     
      #print('g_feedrate now',self._feedrate)  

    def inc_stepXY(self):
      if self._dXY*10.0>C_STEP_MAX:
           self._dXY =C_STEP_MAX
      else:   
           self._dXY *=10.0
      self._state_prev='stepX'     
      #print('g_step+ now',self._dXY)         

    def dec_stepXY(self):
      if self._dXY*0.1<C_STEP_MIN:
           self._dXY =C_STEP_MIN
      else:   
           self._dXY *=0.1
      self._state_prev='stepX'          
      #print('g_step- now',self._dXY)     

    @staticmethod
    def nextStepVals(val, lst):
      idx=0
      if val<lst[0] :
         idx = 0
      elif val>=lst[len(lst)-1] : 
         idx = 0
      else:
          for ii, v in enumerate(lst):
             if ii<len(lst)-1:
                if val>=lst[ii] and val<lst[ii+1]:
                   idx=ii
          idx += 1
      idx %= len(lst)
      return lst[idx]


      


    def stepXY(self):
      self._dXY=self.nextStepVals(self._dXY,DXYZ_STEPS)
      self._state_prev='stepX'          
      #print('g_step _dXY now',self._dXY)     

    def stepZ(self):
      self._dZ=self.nextStepVals(self._dZ,DXYZ_STEPS)
      self._state_prev='stepZ'          
      #print('g_step _dZ now',self._dZ)     

    def set_feedrate(self):
      self._feedrate=self.nextStepVals(self._feedrate, FEED_STEPS)
      self._state_prev='feed'          
      #print('g_feedrate now',self._feedrate) 


    def inc_stepZ(self):
      if self._dXY*10.0>C_STEP_Z_MAX:
           self._dZ =C_STEP_Z_MAX
      else:   
           self._dZ *=10.0
      self._state_prev='stepZ'          
      #print('g_step_z now',self._dZ)         

    def dec_stepZ(self):
      if self._dZ*0.1<C_STEP_Z_MIN:
           self._dZ =C_STEP_Z_MIN
      else:   
           self._dZ *=0.1
      self._state_prev='stepZ'          
      #print('g_step_z now',self._dZ)  

    def set_jog_arrow(self, arrow:str):
      #print('new set_jog_arrow ',arrow)
      self._jog_arrow = arrow
      


    def mpgCommand(self, command:str):
      if DEBUG or (command is not None and command!='' and not command.startswith('?')) :
        print("mpgCommand:",command)

      if not( command.startswith('?') or command.startswith('!') or command.startswith('$') or command.startswith('$')):
        self._execProgress='do'  
      self.uart_grbl_mpg.write(command.encode())
      self.query_now()
      if not command.startswith('?'):
        self.idleCounter = 0

    #jog $J=G91 X0 Y-5 F600
    #$J=G91 X1 F100000

    def grblJog(self, x:float=0.0, y: float=0.0, z:float=0.0):
      f=self.feedrate
      cmd=''
      if x is not None and x!=0.0:
        self.set_jog_arrow(('+' if x>0 else '-')+'x')
        cmd=f'$J=G91 G21 X{x} F{f}'
        #MPG -> <Idle|MPos:30.000,0.000,0.000|Bf:35,1023|FS:0,0,0|Pn:HS|WCO:0.000,0.000,0.000|WCS:G54|A:|Sc:|MPG:1|H:0|T:0|TLR:0|Sl:0.0|FW:grblHAL>
      elif y is not None and y!=0.0:
        self.set_jog_arrow(('+' if y>0 else '-')+'y')
        cmd=f'$J=G91 G21 Y{y} F{f}'
      elif z is not None and z!=0.0:
        self.set_jog_arrow(('+' if z>0 else '-')+'z')
        cmd=f'$J=G91 G21 Z{z} F{f}'
      if cmd !='':
          self.neoLabel(cmd,id='cmd')  
          self.mpgCommand(cmd+'\r\n')
          self.query_now()
          self.neoDisplayJog() 
    
    def toggleMPG(self):
        self.neoLabel("#",id='cmd')
        #self.uart_grbl_mpg.write(bytearray(b'\x8b\r\n'))
        self.uart_grbl_mpg.write(bytearray(b'\x8b'))
        self.query_now()

    def query4MPG(self):
        if self._query4MPG_countDown>0:
           self._query4MPG_countDown -= 1
           self.toggleMPG()

    


    def send2grblOne(self,command:str):
      if DEBUG or (command is not None and command!='' and not command.startswith('?')) :
        print('send2grblOne:',command,len(command))
      if command in ('~','!','?'):
        #self.flashKbdLEDs(LED_ALL , BLINK_2) ##7 - 3 leds       # 1 - macro1
        self.mpgCommand(command)
        if command !='?':
          self.idleCounter = 0
          self.neoLabel(command,id='cmd')
        else:
          if self.editCmd!='':
            self.grblCmd2send=[]
          else: 
             self.idleCounter+=1
             if  self.idleCounter>10:
                self.idleCounter = 0
                self.neoLabel('',id='cmd')
      elif command=='-y':
          self.grblJog(y=-self.step)
      elif  command=='+y':
          self.grblJog(y=self.step)
      elif command=='-x':
          self.grblJog(x=-self.step)
      elif  command=='+x':
          self.grblJog(x=self.step)
      elif command=='-z':
          self.grblJog(z=-self.step)
      elif  command=='+z':
          self.grblJog(z=self.step)
      elif command=='-feed' : 
          self.dec_feedrate()
          self.neoIcon('feed {0:.0f}'.format(self._feedrate))
      elif command=='+feed':
          self.inc_feedrate()
          self.neoIcon('feed {0:.0f}'.format(self._feedrate))
      elif command=='-stepXY' :    
          self.dec_stepXY()
          if self._dXY<1:
            self.neoIcon('dX {0:.1f}'.format(self._dXY).replace('.',','))
          else:  
             self.neoIcon('dX {0:.0f}'.format(self._dXY))
      elif command=='+stepXY' :    
          self.inc_stepXY()
          if self._dXY<1:
            self.neoIcon('dX {0:.1f}'.format(self._dXY).replace('.',','))
          else:  
             self.neoIcon('dX {0:.0f}'.format(self._dXY))
      elif command=='-stepZ' :    
          self.dec_stepZ()
          if self._dZ<1:
            self.neoIcon('dZ {0:.1f}'.format(self._dZ).replace('.',','))
          else:  
             self.neoIcon('dZ {0:.0f}'.format(self._dZ))
      elif command=='+stepZ' :    
          self.inc_stepZ()
          if self._dZ<1:
            self.neoIcon('dZ {0:.1f}'.format(self._dZ).replace('.',','))
          else:  
             self.neoIcon('dZ {0:.0f}'.format(self._dZ))
      elif command=='stepXY' :    
          self.stepXY()
          self.neoIcon('dXY\n{0:.1f}'.format(self._dXY))
      elif command=='stepZ' :    
          self.stepZ()
          self.neoIcon('dZ\n{0:.1f}'.format(self._dZ))
      elif command=='feed' : 
          self.set_feedrate()
          self.neoIcon('feed\n{0:.0f}'.format(self._feedrate))
      elif command=='termLineUp' : 
          self.decTermLinePos()
          if len(self.grbl_info)>0:
            self.neoTerm(self.grbl_info)
      elif command=='termLineDown' : 
          self.incTermLinePos()
          if len(self.grbl_info)>0:
            self.neoTerm(self.grbl_info) 
      elif command=='termLineLeft' : 
          self.decTermPos()
          if len(self.grbl_info)>0:
            self.neoTerm(self.grbl_info)
      elif command=='termLineRight' : 
          self.incTermPos()
          if len(self.grbl_info)>0:
            self.neoTerm(self.grbl_info)           
      elif command=='termHome' : 
          self.homeTermPos()
          if len(self.grbl_info)>0:
            self.neoTerm(self.grbl_info)   
      elif command in ('#'):  
        self.toggleMPG()
      elif command in ('cancel'):  
        # if self.state == 'run' or self.state == 'jog':
          #self.flashKbdLEDs(LED_SCROLLLOCK , BLINK_5) ##2 - leds ???       # 2 - macro1 10/2 blink
          self.uart_grbl_mpg.write(bytearray(b'\x85\r\n')) #Jog Cancel
          self.uart_grbl_mpg.write(bytearray(b'\x18\r\n')) # cancel ascii ctrl-x
          self.neoLabel(command,id='cmd')
          self.query_now(1)
        # else:
          #self.flashKbdLEDs(LED_ALL , BLINK_2) ##7 - 3 leds       # 1 - macro1
          # pass 
      elif command in ('reset'):  
          self.uart_grbl_mpg.write(bytearray(b'\x85\r\n')) #Jog Cancel
          self.uart_grbl_mpg.write(bytearray(b'\x18\r\n')) # cancel ascii ctrl-x
          self.neoLabel(command,id='cmd')
          self.query_now(2)
          microcontroller.reset()
      elif command in ('help'):  
          self.neoIcon(self.getHelp())
      elif command in ('^'):  
        #self.flashKbdLEDs(LED_ALL , BLINK_2) ##7 - 3 leds       # 1 - macro1
        self.neoLabel('$X',id='cmd')
        self.uart_grbl_mpg.write('$X'.encode()+b'\r\n')
        self.query_now()
      else:
        if command.strip()!='':
            # self.neoInfo(command[:10],virtual_width = 128)
            self.neoLabel(command,id='cmd')
            self.uart_grbl_mpg.write(command.encode()+b'\r\n')
            if not(command.startswith('?') or command.startswith('!') or command.startswith('$') or command.startswith('$') or command.startswith('#')):
                self._execProgress='do'

            cnt=0
            for cc in self.grblCmdHist:
                if cc==self.editCmd:
                    cnt=1
                    break
            if cnt<1:   
                if len(self.grblCmdHist)>20:
                    self.grblCmdHist.pop(-1)
                self.grblCmdHist.append(command)
                self.grblCmd2HistPos  = len(self.grblCmdHist)-1
            self.neoLabel(self.editCmd,id='cmd')
  

    def send2grbl(self,command:str):        
      #if DEBUG or (command is not None and command!='' and not command.startswith('?')) :
      #  print('send2grbl:',command,' queueLen=',len(self.grblCmd2send), self._execProgress)
      self.grblCmd2send.append(command)
      if self._execProgress!='do':
          self.popCmd2grbl()

    def popCmd2grbl(self):
      if len(self.grblCmd2send)>0:
        l_cmd=self.grblCmd2send[0]
        if self._execProgress == 'do' and (
          l_cmd=='-y' or l_cmd=='+y' or 
          l_cmd=='-x' or l_cmd=='+x' or 
          l_cmd=='-z' or l_cmd=='+z' ):
          print('popCmd2grbl: busy', self._execProgress, l_cmd )
          return
        else:
          l_cmd=self.grblCmd2send.pop(0)
          self.send2grblOne(l_cmd)

    def getHist(self, diff=1):
          if len(self.grblCmdHist)>0:
             self.grblCmd2HistPos+=diff
             self.grblCmd2HistPos%=len(self.grblCmdHist)
             return self.grblCmdHist[self.grblCmd2HistPos]
          else:
             print('history is empty')              
             return ''

    @property
    def feedrate(self):
        return self._feedrate  
    
    
    def query_now(self, interval=0.2):
        self._need_query = True
       
    @property
    def need_query(self):
        # l_nq = self._need_query or time.monotonic()-self.start_time_q>GRBL_QUERY_INTERVAL
        l_nq = self._need_query or time.monotonic()>self.time2query
        if l_nq:
          self.time2query = time.monotonic()+GRBL_QUERY_INTERVAL
        self._need_query = False
        return l_nq
    

    @property
    def step(self):
        return self._dXY          

    @property
    def mpg(self):
        return self._mpg    
    @property
    def mpg_prev(self):
        return self._mpg_prev
    
    @property
    def state(self):
        return self._state  
    
    @property
    def state_prev(self):
        return self._state_prev     
    
    def state_is_changed(self):
        l_changed = self._state_is_changed
        self._state_is_changed = False
        return l_changed
        
            
    #MPG -> <Idle|MPos:30.000,0.000,0.000|Bf:35,1023|FS:0,0,0|Pn:HS|WCO:0.000,0.000,0.000|WCS:G54|A:|Sc:|MPG:1|H:0|T:0|TLR:0|Sl:0.0|FW:grblHAL>
    def parseState(self,grblState:str):
      try:
        ii=0
        token =''
        if grblState is None:
          self._state_code='empty'
          return
        grblState=grblState.strip()
           
        



        #print('grblState IN ',grblState,']]]]]]]]]]]]]',grblState.find('error:'))  
        grblState=grblState.replace('ok','').replace('\n','').replace('\r','')
        self._state_code='parse'
        if grblState.find('error:')>=0:
          print('ERRor',grblState,']]]]]]]]]]]]]')  
          self._execProgress='error'
          self._state=grblState
          self._state_is_changed = (self._state_prev is None or  self._state_prev != self._state)
          self._state_prev = self._state
          self._state_time_change = time.monotonic()
          self._state_code='error'
          return        
        elif grblState.find('alarm:')>=0:
          print('ALarm',grblState,']]]]]]]]]]]]]')  
          self._execProgress='alarm'
          self._state=grblState
          self._state_is_changed = (self._state_prev is None or  self._state_prev != self._state)
          self._state_prev = self._state
          self._state_time_change = time.monotonic()
          self._state_code='alarm'
          return        
        elif grblState.find('<')>=0 and grblState.find('>')>=0 and  grblState.find('<')<grblState.find('>')>=0 :
            self.grbl_state = grblState[grblState.find('<')+1:grblState.find('>')]
            for ii,token in enumerate(self.grbl_state.lower().split('|')):
                if ii==0 :
                  prv = self._state_prev
                  self._state_prev = self._state
                  self._state = token
                  self._state_is_changed = (prv is None or  prv != self._state)
                  if self._execProgress=='do' and (self._state.startswith('idle') or self._state.startswith('alarm')) :
                     self._execProgress='done'
                  self._state_time_change = time.monotonic()
                else:
                    elem = token.split(':')
                    if len(elem)>1 and elem[0]=='mpg' and elem[1] is not None and (elem[1]=='1' or elem[1]=='0'):
                        self._mpg_prev=self._mpg
                        self._mpg=(elem[1]=='1')
                        self.labels['info'].color=VFD_PURPLE if self._mpg  else VFD_WHITE
                    elif  len(elem)>1 and elem[0]=='mpos' and elem[1] is not None:       
                        xyz = elem[1].split(',')
                        #print('xyz',xyz)
                        if len(xyz)==3:
                          self._mX, self._mY,self._mZ = [ float(xx) for xx in xyz ]
                        elif len(xyz)==4:
                          self._mX, self._mY,self._mZ,self._mA = [ float(xx) for xx in xyz ]  
                        elif len(xyz)==5:
                          self._mX, self._mY,self._mZ,self._mA,self._mB = [ float(xx) for xx in xyz ]  
                        elif len(xyz)==6:
                          self._mX, self._mY,self._mZ,self._mA,self._mB,self._mC = [ float(xx) for xx in xyz ]  
            self._state_code='done'
            return
        
        elif grblState.find('[')>=0 and grblState.find(']')>=0 and  grblState.find('[')<grblState.find(']')>=0 :
            grblState=grblState[grblState.find('['):grblState.find('[')+1]
            self.grbl_info=grblState
            if grblState.count('Unlocked')>0:
              prv = self._state_prev
              self._state_prev = self._state
              self._state = 'unlocked'
              self._state_is_changed = (prv is None or  prv != self._state)
              self._execProgress='done'
            self._state_code='done'  
            return
        elif grblState.startswith('$'):
          self.grbl_info=grblState
          self._state_code='done'  
          return 

           #self.term_line_from=1
        elif grblState.find('ok'):
          self._execProgress='ok'
          self._state='ok'
          self._state_is_changed = (self._state_prev is None or  self._state_prev != self._state)
          self._state_prev = self._state
          self._state_time_change = time.monotonic()
          self._state_code='done'
          return
        elif  grblState.startswith('$')  :
          self.grbl_info=grblState           
          self._state_code='done'
          return
        else:
          l_cntNewL=grblState.count('\n')
          if l_cntNewL>0:
              if grblState.count('ok')>0:
                  self._execProgress='ok'
          self._state_code='done'
          return
        
            
              

 
        
        



      except:
          print('error parseState ',grblState, ii, token)
          self._state_code='fail'  
                      


    def displayState(self,grblState:str):     
      self.parseState(grblState.strip('\x00').strip())
      # print("MPG ->",grblState,' \n - >> prev ',self.state_prev, self.mpg_prev,' now=>',self.state, self.mpg)
      self.neoLabel(self.grbl_state,id='info')
      
      if len(self.grbl_info)>0:
         self.neoTerm(self.grbl_info)
         
      self.neoLabel('',id='x')
      self.neoLabel('',id='y')
      self.neoLabel('',id='z')
      
      
      if self.mpg is not None and (self.mpg_prev is None or self.mpg !=self.mpg_prev):
          self._mpg_prev=self._mpg
      if self.state_is_changed() or self.state == 'idle' or self.state.startswith('hold') :  
              if self.state.startswith('alarm'):
                  self._jog_arrow = ''
                  self.neoDisplayJog()
                  self.neoIcon('Alarm\n^\nshft+6')
                  self.neoLabel(self.state,id='state')
              elif self.state == 'run':    
                  self.neoLabel(self.state,id='state')
                  self.neoIcon('\n  Run')
              elif self.state == 'jog':    
                  self.neoLabel(self.state,id='state')
                  self.neoDisplayJog()
                  self.neoIcon('\n  Jog')
              elif self.state=='unlocked':
                  self.neoLabel(self.state,id='state')
              elif self.state=='hold:1':
                  self.neoLabel(self.state,id='state')
              elif self.state=='hold:0':
                  #self.flashKbdLEDs(LED_NUMLOCK , BLINK_5)
                  # self.neoInfo(self.state)  
                  self.neoLabel(self.state,id='state')
              elif self.state.startswith('error'): 
                  self._jog_arrow = ''
                  self.neoDisplayJog() 
                  # self.neoError('err')  
                  #self.flashKbdLEDs(LED_CAPSLOCK , BLINK_5) 
                  self.neoLabel(self.state,id='state')
              elif self.state == 'idle' :
                  self._jog_arrow = ''
                  self.neoDisplayJog()    
                  #self.flashKbdLEDs(LED_ALL , NOBLINK) 
                  # self.neoIdle()
                  self.neoLabel(self.state,id='state')
    




    def neoDisplayJog(self) :     
        color=X_ARROW_COLOR
        if self._jog_arrow[-1:]=='y':
           color=Y_ARROW_COLOR
        elif self._jog_arrow[-1:]=='z':  
           color=Z_ARROW_COLOR
        if self._jog_arrow=='':
           self.neoIcon(text='   ')   
        else:
          self.neoIcon(text=('>>>' if self._jog_arrow.startswith('+') else '<<<') +
                       '\n'+('d={0:.1f}'.format(self._dZ) if self._jog_arrow.endswith('z') else 'd={0:.1f}'.format(self._dXY))+
                       '\nf={0:.0f}'.format(self._feedrate)
                       ,color=color)   



    def setEdit(self, text):
       self.editCmd=text

    def neoShowEdit(self):
      self.idleCounter = 0
      # self.neoIdle()
      self.neoLabel(text=self.editCmd,id='cmd')
                                

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
        self.grblStateObj.setEdit(self.grblCommand)

 
    @staticmethod
    def chars2Grbl(charIn:str): 
        return KBD2GRBL.get(charIn,charIn)
    
    def backspace(self):
        self.grblCommand =self.grblCommand[0:-1]
        self.grblStateObj.setEdit(self.grblCommand)

    
    def put_char(self, char):
        self.grblCommand +=char
        self.grblStateObj.setEdit(self.grblCommand)

    def space(self):
        self.put_char(' ')  
        self.grblStateObj.setEdit(self.grblCommand)


    def clear(self):
        self.grblPrevCommand=self.grblCommand
        self.grblCommand = ''
        self.grblStateObj.setEdit(self.grblCommand)  

    def set_macro(self, key:str):
        self.grblMacro[key]=self.grblCommand
        self.clear()

        
    def get_macro(self, key:str):
        self.clear()
        self.grblCommand=self.grblMacro.get(key,'')
        self.grblStateObj.setEdit(self.grblCommand)
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
        if charIn =='enter' :
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
            #   print('proceedChars: l_char=',l_char)
            self.proceedOneChar(l_char)


#todo 
# hard beats every send ? or state changes        
# rapid commands
#1681920
#1681408

