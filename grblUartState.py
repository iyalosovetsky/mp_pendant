import time
import machine

from machine import UART

#import uasyncio as asyncio
#from nanoguilib.color_setup import ssd
from nanoguilib.writer import CWriter
from nanoguilib.meter import Meter
from nanoguilib.label import Label

# Fonts
import nanoguilib.arial10 as arial10
import nanoguilib.courier20 as fixed
import nanoguilib.font6 as small

BLINK_2 = 1
BLINK_5 = 2
BLINK_INFINITE = 3
NOBLINK = 4
 
X_ARROW_COLOR = 'red'
Y_ARROW_COLOR = 'green'
Z_ARROW_COLOR = 'blue'

DEBUG= False

VFD0_PURPLE = 0x00FFD2
VFD0_GREEN = 0x30BF30
VFD0_RED = 0xCF3030
VFD0_BLUE = 0x4040CF
VFD0_YELLOW = 0xFFFF00
VFD0_YELLOW2 = 0xBFBF00
VFD0_WHITE = 0xCFCFCF



VFD_PURPLE = 0xFFD2
VFD_GREEN = 0x0011
VFD_RED = 0x07E0
VFD_BLUE = 0xf800
VFD_YELLOW = VFD_GREEN | VFD_RED
VFD_YELLOW2 = VFD_YELLOW-12
VFD_WHITE = 0xffff
VFD_BLACK = 0x0000


VFD_ARROW_X = VFD_RED
VFD_ARROW_Y = VFD_GREEN
VFD_ARROW_Z = VFD_BLUE
VFD_BG = VFD_BLACK






#GRBL_QUERY_INTERVAL = 0.5
#GRBL_QUERY_INTERVAL_IDLE = 10
GRBL_QUERY_INTERVAL_IDLE = 10000000000  # 10s in nanoseconds
GRBL_QUERY_INTERVAL_RUN = 500000000  # 0.5s in nanoseconds

C_STEP_MAX = 100.0
C_STEP_MIN = 0.1

C_STEP_Z_MAX = 20.0
C_STEP_Z_MIN = 0.1

C_FEED_MAX = 2000.0
C_FEED_MIN = 200.0

DXYZ_STEPS=[0.1,1.,10.,50.]
FEED_STEPS=[10.,100.,200.,500.,1000.]


objgrblState=None
rx_buffer = b''

#def uart_callback(uart_object):
#    global rx_buffer
#    # Read all available bytes from the UART buffer
#    # It's better to use uart.read() without an argument to get all data at once
#    # or iterate until uart.any() is 0.
#    while uart_object.any() > 0:
#        #byte = uart_object.read(1) # Read a single byte
#        if byte is not None:
#            rx_buffer += byte


def uart_callback(uart_object):
    global objgrblState
    global rx_buffer
    # Read all available bytes from the UART buffer
    # It's better to use uart.read() without an argument to get all data at once
    # or iterate until uart.any() is 0.
    while uart_object.any() > 0:
        byte_data = uart_object.read(1) # Read a single byte
        
        if byte_data is not None:
            #print(f"Received byte (bytes object): {byte_data}, Integer value: {byte_value}, Character: {chr(byte_value)}")
            if (byte_data[0] == 10 or  byte_data[0]==13):
              if len(rx_buffer)>0:  
                  if objgrblState is not None:
                    objgrblState.procUartInByte(rx_buffer)
                  rx_buffer = b''
            else:
              rx_buffer += byte_data

        
        



        

class NeoLabelObj(object):
    def __init__(self, color:int , scale:float,x:int,y:int,text:str = '',label=None,fldLabel=None):
        self.x= x
        self.y= y
        self.text=  text
        self.scale= scale
        self.color= color
        self.label= label
        self.fldLabel = fldLabel
        

class GrblState(object):
    def __init__(self,uart_grbl_mpg,neo,
                  state:str = '', 
                  mpg:bool = None,
                  debug:bool = DEBUG,
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
        DEBUG = debug
        self.debug = debug
        



        
        self._error = ''
        self._alarm = ''
        self._need_query = True
        self.gotQuery = False
       

        self.query_now('init2')
        self._query4MPG_countDown = 2
        self.time2query = time.time_ns()
        self.timeDelta2query = GRBL_QUERY_INTERVAL_IDLE
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
        
        #uarIn
        self.uart_grbl_mpg = uart_grbl_mpg
        self.uartInNewData=-1
        self.bufferUartIn=['','','',''] #
        self.bufferUartPos=0
        self.bufferUartPrev=0
        global objgrblState
        objgrblState=self
        # Set up the interrupt handler
        # Use UART.IRQ_RXIDLE or UART.IRQ_RX depending on board availability and requirement
        # IRQ_RX triggers on each received character (if supported)
        # IRQ_RXIDLE triggers when the line is idle after receiving at least one character


        


        
        if  self.uart_grbl_mpg!=None :
            self.uart_grbl_mpg.irq(handler=uart_callback, trigger=UART.IRQ_RXIDLE, hard=False) # 'hard=False' is often required
       
       
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
        self.neo_refresh= False
        self._state_time_change = time.time_ns()
        self._msg_conf = [
            ('x', '     '        , VFD_GREEN,  200, 15, 3,320-200-2),
            ('y', '     '          , VFD_PURPLE,  200, 55, 3,320-200-2),
            ('z', '     '         , neo.rgb(5,10,30),  200, 95, 3,320-200-2),
            ('cmd', '     '      , VFD_WHITE,    0, 170, 2,320),
            ('state', '     '    , VFD_WHITE,  190, 130, 2,320-210),
            ('icon', 'grbl',      VFD_PURPLE,    0,  20, 4,180),
            ('term', '\nF1\nHelp', VFD_WHITE,    0,  40, 2,180),
            ('info', '    '      , VFD_WHITE,    0, 200, 1,320)
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
        wriNowrap = CWriter(neo, fixed, verbose=self.debug)
        wriNowrap.set_clip(False, False, False) #row_clip=None, col_clip=None, wrap=None
        wriNowrapArial = CWriter(neo, arial10, verbose=self.debug)
        wriNowrapArial.set_clip(False, False, False) #row_clip=None, col_clip=None, wrap=None
        
        wriWrap = CWriter(neo, fixed, verbose=self.debug)
        wriWrap.set_clip(False, False, True) #row_clip=None, col_clip=None, wrap=None
        
        for c1 in self._msg_conf:
            (name, textline, color, x, y, scale, width) = c1  # unpack tuple into five var names
            
            #l_label = label.Label(terminalio.FONT, text=textline, color=color, scale=scale)
            #l_label={"x":x,"y":y,"text":textline,"color":color,"scale":scale}
            #l_label.x = x
            #l_label.y = y
            #self.labels[name] = l_label
            #self.neo.display.root_group.append(l_label)
            if name in ('xyz'):
              flw=wriNowrap.stringlen(name)
              fl=Label(wriNowrap, y, x, flw,fgcolor=color)
              fl.value(name)
              ll=Label(wriNowrap, y, x+flw, width-flw, bdcolor=None)
              ll.value('{:6.2f}'.format(-123.02))
              self.labels[name] = NeoLabelObj(text  = textline, color=color , scale=scale,x=x,y=y,label=ll,fldLabel=fl)
            elif name in ('info'):
              ll=Label(wriNowrapArial, y, x, width-30,fgcolor=color,bgcolor=VFD_BG)
              if textline.strip()!='':
                  ll.value(textline)
              else:    
                ll.value(name)
              self.labels[name] = NeoLabelObj(text  = textline, color=color , scale=scale,x=x,y=y,label=ll)
            elif name in ('cmd','icon','state'):
              ll=Label(wriNowrap, y, x, width-30,fgcolor=color,bgcolor=VFD_BG)
              if textline.strip()!='':
                  ll.value(textline)
              else:    
                ll.value(name)
              self.labels[name] = NeoLabelObj(text  = textline, color=color , scale=scale,x=x,y=y,label=ll)
            else: #term etc
              ll=Label(wriWrap, y, x, width-30,fgcolor=color,bgcolor=VFD_BG)
              if textline.strip()!='':
                  ll.value(textline)
              else:    
                ll.value(name)
              self.labels[name] = NeoLabelObj(text  = textline, color=color , scale=scale,x=x,y=y,label=ll)

        self.neo_refresh= True
        #self.hello()
        

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
            
        
    def neoDraw(self,id):
        if id is not None:
            if DEBUG:
                print('neoDraw['+id+']',self.labels[id].x,self.labels[id].y,self.labels[id].color,self.labels[id].text)
            self.labels[id].label.value(self.labels[id].text)
            self.neo_refresh= True
            
            #self.neo.text(self.labels[id].text,self.labels[id].x,self.labels[id].y,self.labels[id].color)
            #self.neo.show_up()
        #self.RED   =   0x07E0
        #self.GREEN =   0x001f
        #self.BLUE  =   0xf800
        #self.WHITE =   0xffff
        #self.BLACK =   0x0000            
            

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
        l_id=id
        if id=='x':
          self.labels[id].text = '{0:.3f}'.format(self._mX)
          self.labels[id].color=VFD_ARROW_X
        elif id=='y':
          self.labels[id].text = '{0:.3f}'.format(self._mY)  
          self.labels[id].color=VFD_ARROW_Y
        elif id=='z':
          self.labels[id].text = '{0:.3f}'.format(self._mZ)  
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
        else:
            l_id=None
        self.neoDraw(l_id)       

             
    def hello(self):
       self.neo.fill(VFD_BG)
       self.neo.fill_rect(60,5,200,30,self.neo.RED)
       self.neo.text('GrblHAL v'+self.__version__,90,17,self.neo.WHITE)
       display_color = 0x001F
       for i in range(0,12): 
           self.neo.fill_rect(i*20+30,100,30,50,(display_color))
           display_color = display_color << 1
       self.neo.show_up()
       time.sleep(0.5)
       self.neo.fill(VFD_BG)

       self.neoLabel('GrblHAL v'+self.__version__,id='cmd',color=VFD_YELLOW)
       

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
      if not command.startswith('?'):
          self.query_now('mpgCommand')
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
          self.query_now('grblJog')
          if self.timeDelta2query != GRBL_QUERY_INTERVAL_RUN:
              self.timeDelta2query = GRBL_QUERY_INTERVAL_RUN
          if self.time2query > time.time_ns()+self.timeDelta2query:
              self.time2query = time.time_ns()+self.timeDelta2query
          
          self.neoDisplayJog() 
    
    def toggleMPG(self):
        self.neoLabel("#",id='cmd')
        #self.uart_grbl_mpg.write(bytearray(b'\x8b\r\n'))
        self.uart_grbl_mpg.write(bytearray(b'\x8b'))
        self.query_now('toggleMPG')

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
          self.gotQuery=True  
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
          self.query_now('cancel')
        # else:
          #self.flashKbdLEDs(LED_ALL , BLINK_2) ##7 - 3 leds       # 1 - macro1
          # pass 
      elif command in ('reset'):  
          self.uart_grbl_mpg.write(bytearray(b'\x85\r\n')) #Jog Cancel
          self.uart_grbl_mpg.write(bytearray(b'\x18\r\n')) # cancel ascii ctrl-x
          self.neoLabel(command,id='cmd')
          self.query_now('reset')
          machine.soft_reset()
      elif command in ('help'):  
          self.neoIcon(self.getHelp())
      elif command in ('^'):  
        #self.flashKbdLEDs(LED_ALL , BLINK_2) ##7 - 3 leds       # 1 - macro1
        self.neoLabel('$X',id='cmd')
        self.uart_grbl_mpg.write('$X'.encode()+b'\r\n')
        self.query_now('$X')
      else:
        if command.strip()!='':
            # self.neoInfo(command[:10],virtual_width = 128)
            self.neoLabel(command,id='cmd')
            self.uart_grbl_mpg.write(command.encode()+b'\r\n')
            if not(command.startswith('?') or command.startswith('!') or command.startswith('$') or command.startswith('$') or command.startswith('#')):
                self._execProgress='do'
                if self.timeDelta2query != GRBL_QUERY_INTERVAL_RUN:
                  self.timeDelta2query = GRBL_QUERY_INTERVAL_RUN
                if self.time2query > time.time_ns()+self.timeDelta2query:
                  self.time2query = time.time_ns()+self.timeDelta2query


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
    
    
    def query_now(self, partent):
        if self.debug:
            print('query_now',partent)
        self.gotQuery = False
       
    @property
    def need_query(self):
        # l_nq = self._need_query or time.time_ns()-self.start_time_q>GRBL_QUERY_INTERVAL
        #l_nq = self._need_query or time.time_ns()>self.time2query
        l_nq = self._need_query or (time.time_ns()>self.time2query)
        #print('l_nq=',l_nq,self.time2query > time.time_ns(),self.time2query , time.time_ns())
        if l_nq:
          if self.gotQuery:
              if time.time_ns()>self.time2query:
                  self.time2query = time.time_ns()+self.timeDelta2query
              self.gotQuery=False
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
          self._state_time_change = time.time_ns()
          self._state_code='error'
          return        
        elif grblState.find('alarm:')>=0:
          print('ALarm',grblState,']]]]]]]]]]]]]')  
          self._execProgress='alarm'
          self._state=grblState
          self._state_is_changed = (self._state_prev is None or  self._state_prev != self._state)
          self._state_prev = self._state
          self._state_time_change = time.time_ns()
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
                     self.time2query = time.time_ns()+self.timeDelta2query
                    
                  if (self._state.startswith('run') or self._state.startswith('jog')) :
                      if self.timeDelta2query != GRBL_QUERY_INTERVAL_RUN:
                          self.timeDelta2query = GRBL_QUERY_INTERVAL_RUN
                      if self.time2query > time.time_ns()+self.timeDelta2query:
                          self.time2query = time.time_ns()+self.timeDelta2query
                      
                  elif  self._state_is_changed :
                      self.time2query = time.time_ns()+GRBL_QUERY_INTERVAL_RUN
                  elif not (self._state.startswith('run') or self._state.startswith('jog')) :
                      self.timeDelta2query = GRBL_QUERY_INTERVAL_IDLE
          

                  
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
          self._state_time_change = time.time_ns()
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
      

    def procUartInByte(self,chars):
      # Process the bytes (e.g., print its integer value or character)
      if len(chars)>0:
            if self.debug:
                print('chars',chars.decode())
            
            #print(f"Received byte (bytes object): {byte_data}, Integer value: {byte_value}, Character: {chr(byte_value)}")
            self.bufferUartIn[self.bufferUartPos]=chars.decode()
            self.displayState(self.bufferUartIn[self.bufferUartPos])
            self.bufferUartPrev=self.bufferUartPos
            if self.bufferUartPos>=len(self.bufferUartIn)-1:
                self.bufferUartPos=0
            else:    
                self.bufferUartPos+=1
            self.uartInNewData=self.bufferUartPrev    # new line in cycle buffer
            
            
    def procUartGetLastData(self, printEnable=False):
        if self.uartInNewData>=0:
            self.uartInNewData=-1
            if printEnable and self.bufferUartIn[self.uartInNewData]!='':
                print(self.bufferUartIn[self.uartInNewData])
            return self.bufferUartIn[self.uartInNewData]
        return None
        
      


