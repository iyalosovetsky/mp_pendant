import time
import machine

from machine import UART

#import uasyncio as asyncio
#from nanoguilib.color_setup import ssd
from nanoguilib.writer import CWriter
from nanoguilib.meter import Meter
from nanoguilib.label import Label, ALIGN_LEFT, ALIGN_RIGHT, ALIGN_CENTER 
from nanoguilib.textbox import Textbox

# Fonts
import nanoguilib.arial10 as arial10
import nanoguilib.courier20 as fixed
import nanoguilib.arial35 as arial35
#import nanoguilib.font6 as small

BLINK_2 = 1
BLINK_5 = 2
BLINK_INFINITE = 3
NOBLINK = 4
 
X_ARROW_COLOR = 'red'
Y_ARROW_COLOR = 'green'
Z_ARROW_COLOR = 'lblue'
ICON_COLOR = 'white'

DEBUG= False

VFD0_PURPLE = 0x00FFD2
VFD0_GREEN = 0x30BF30
VFD0_RED = 0xCF3030
VFD0_BLUE = 0x4040CF
VFD0_YELLOW = 0xFFFF00
VFD0_YELLOW2 = 0xBFBF00
VFD0_WHITE = 0xCFCFCF


VFD_GRAY = 0x0016 #0x0019 0x001A 0x0006 0x0009
VFD_PURPLE = 0x0017 #0x0007
VFD_GREEN = 0x0011 #0x0001 0x0021
VFD_RED = 0x0002
VFD_LBLUE = 0x0008 #0x0018
VFD_BLUE = 0x0004 #0x0014
VFD_YELLOW = 0x0005 #0x0015 ssd.rgb(0xFF,0xff,0x00)
VFD_YELLOW2 = VFD_YELLOW-12
VFD_WHITE = 0xffff
VFD_BLACK = 0x0000


VFD_ARROW_X = VFD_RED
VFD_ARROW_Y = VFD_GREEN
VFD_ARROW_Z = VFD_BLUE
VFD_LABEL_X = VFD_WHITE
VFD_LABEL_Y = VFD_WHITE
VFD_LABEL_Z = VFD_WHITE
VFD_BG = VFD_BLACK






#GRBL_QUERY_INTERVAL = 0.5
#GRBL_QUERY_INTERVAL_IDLE = 10
GRBL_QUERY_INTERVAL_IDLE = 10000000000  # 10s in nanoseconds
GRBL_QUERY_INTERVAL_RUN = 500000000  # 0.5s in nanoseconds
MPG_INTERVAL = 500000000  # 0.5s in nanoseconds
ROTARY_DUMP2_JOG_INTERVAL = 600000000  # 0.6s in nanoseconds
POP_CMD_GRBL_INTERVAL =  200000000 # 0.2s in nanoseconds for pop cmd to grbl
RUN_NOW_INTERVAL =  200000000 # 0.2s in nanoseconds for pop cmd to grbl
PENDANT_READ_INTERVAL =  300000000 # 0.3s in nanoseconds for pop cmd to grbl


MAX_BUFFER_SIZE = 200

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
            if (byte_data[0] == 10 or  byte_data[0]==13 or len(rx_buffer)> MAX_BUFFER_SIZE):  # Newline or carriage return or buffer full):
              if len(rx_buffer)>0:  
                  if objgrblState is not None:
                    try:  
                        objgrblState.procUartInByte(rx_buffer)
                    except:
                        print("cannot proc line len=",len(rx_buffer))
                  rx_buffer = b''
            else:
              rx_buffer += byte_data
                  

        
        

def color2rgb(color:str):
    if color is not None and isinstance(color,str):
        if color.lower() == 'red':
          color = VFD_RED
        elif color.lower() == 'green':   
          color = VFD_GREEN
        elif color.lower() == 'blue':   
          color = VFD_BLUE
        elif color.lower() == 'lblue':   
          color = VFD_LBLUE
        elif color.lower() == 'purple':   
          color = VFD_PURPLE      
        elif color.lower() == 'yellow':   
          color = VFD_YELLOW      
        elif color.lower() == 'white':   
          color = VFD_WHITE
        else:
           color = VFD_WHITE   
    return  color

        

class NeoLabelObj(object):
    def __init__(self, color:int , scale:float,x:int,y:int,text:str = '',label=None,fldLabel=None,
                 width:int=100,oneWidth:int=20, nlines:int=1, align = ALIGN_LEFT ):
        self.x= x
        self.y= y
        self.text=  text
        self.scale= scale
        self.color= color
        self.nlines = nlines  
        self.label= label
        self.width= self.label.width
        self.height= self.label.height
        self.oneWidth= oneWidth
        self.charsl=5
        self.hidden = False
        self.align =  align
        self.chars = 5
        if self.width is not None and self.oneWidth is not None and self.oneWidth>0 and self.width>0 :
          # self.charsl=self.width//self.oneWidth + (1 if (self.width%self.oneWidth)>0 else 0)
          self.charsl=self.width//self.oneWidth 
          self.chars =self.charsl * self.nlines
        
        self.fldLabel = fldLabel
        

class GrblState(object):
    __version__ = '0.1'
    rt={} # real time tasks

    helpIdx=-1
    _mX:float = 0.0
    _mY:float = 0.0
    _mZ:float = 0.0
    _mA:float = 0.0
    _mB:float = 0.0
    _mC:float = 0.0

    _mX_prev:float = 0.0
    _mY_prev:float = 0.0
    _mZ_prev:float = 0.0
    _mA_prev:float = 0.0
    _mB_prev:float = 0.0
    _mC_prev:float = 0.0
    _mpos_changed:bool  = False

    _mPosInited:bool = False
    #work coordinate offset (WCO). Used to calculate WPos from MPos 
    _wX:float = 0.0
    _wY:float = 0.0
    _wZ:float = 0.0
    _wA:float = 0.0
    _wB:float = 0.0
    _wC:float = 0.0

    _wX_prev:float = 0.0
    _wY_prev:float = 0.0
    _wZ_prev:float = 0.0
    _wA_prev:float = 0.0
    _wB_prev:float = 0.0
    _wC_prev:float = 0.0
    _wpos_changed:bool  = False

    _dXY:float = DXYZ_STEPS[1]
    _dZ:float = DXYZ_STEPS[1]
    _feedrate:float =  FEED_STEPS[2]
    _mpg:bool = None
    neo = None
    neo_refresh:bool = False
    _pressedArea:str= None
    _pressedX:int= None
    _pressedY:int= None
    _pressedOldX:int= None
    _pressedOldY:int= None

    debug:bool = DEBUG 
    _error:str = ''
    _alarm:str = ''
    
    _state:str = 'Idle'
    _state_prev:str = 'unk'
    _parse_state_code:str='init'
    sendedQuery2grblCounter:int = 0
    
    _query4MPG_countDown:int = 10
    # time2query:int = time.time_ns()
    # MPG_time2query:int = time.time_ns()
    # timeDelta2query:int = GRBL_QUERY_INTERVAL_IDLE
    _state_is_changed:bool = False
    _state_time_change:int = time.time_ns()
    grbl_display_state:str = '' # text in chevron
    grbl_info:str = '' # text in bracket
    _grblExecProgress:str = 'init'
    # gotQuery:bool = False




    
    _mpg_prev:str = ''
    uartInNewData:int = -1
    bufferUartIn=['','','',''] #
    bufferUartPos:int = 0
    bufferUartPrev:int = 0
    rotaryObj=[{'obj':None ,'axe':'x','unit':1.0, 'value':0,'value_prev':0,'mpos':0,'nanosec':0, 'scale':1.0 },
               {'obj':None ,'axe':'y','unit':1.0, 'value':0,'value_prev':0,'mpos':0,'nanosec':0, 'scale':1.0 }]


    editCmd:str = ''
    # statetext:str = ''
    # prev_statetext:str  = ''
    grblCmd2send=[]
    grblCmdHist=[]
    grblCmd2HistPos:int = 0
    term_line_from:int = 1
    term_pos_from:int = 0

    _jog_arrow:str = ''

    _ui_modes=['main','drive','feedMov','feedDrv','confirm'] #confirm must be last
    _ui_mode=0
    _ui_confirm='unkn'

    


    
    def __init__(self,uart_grbl_mpg,
                  neo,
                  debug:bool = DEBUG,
                  ) :
        global objgrblState
        objgrblState=self
        self.rt['upd_rotary'] = {'last_start': time.time_ns (), 'interval': ROTARY_DUMP2_JOG_INTERVAL, 'proc': self.upd_rotary , 'last_error': 0}
        self.rt['query4MPG'] = {'last_start': time.time_ns (), 'interval': MPG_INTERVAL, 'proc': self.query4MPG , 'last_error': 0}
        self.rt['popCmd2grbl'] = {'last_start': time.time_ns (), 'interval': POP_CMD_GRBL_INTERVAL, 'proc': self.popCmd2grbl , 'last_error': 0}
        self.rt['autoQuery2grbl'] = {'last_start': time.time_ns (), 'interval': GRBL_QUERY_INTERVAL_IDLE, 'proc': self.autoQuery2grbl , 'last_error': 0}
        
        # if st.need_query:
    #     st.send2grblOne('?') # get status from grbl cnc machine    



        self.debug = debug
        
        self.neo = neo
        #uarIn
        self.uart_grbl_mpg = uart_grbl_mpg
        



        
        
       
       

        self.query_now('init2')
        # self.time2query = time.time_ns()
        # self.MPG_time2query = time.time_ns()
        




        


        
        if  self.uart_grbl_mpg!=None :
            self.uart_grbl_mpg.irq(handler=uart_callback, trigger=UART.IRQ_RXIDLE, hard=False) # 'hard=False' is often required
       
       
        self.neoInit()
        

        #self.hello()
        
    #main real time loop
    def p_RTLoop(self):
        for key, value in self.rt.items ():
            l_time = time.time_ns ()
            l_timeprev = value['last_start']
            if value['proc'] is not None:
                if (((l_time - l_timeprev) > value['interval'])) :
                    value['last_start'] = l_time
                    try:  
                        value['last_error'] = value['proc'] ()
                        if value['last_error'] is None:
                            value['last_error'] = 0
                    except Exception as e:
                        value['last_error'] = -97
                        print ('error rt ' + key, e)
    # real time task to set last_start to now to run immediately
    def p_RTSetRunNow(self,id:str):
        if id in self.rt:
            if self.rt[id]['interval'] > RUN_NOW_INTERVAL:
              self.rt[id]['last_start'] = time.time_ns() - (self.rt[id]['interval'] - RUN_NOW_INTERVAL)
            else:
               self.rt[id]['last_start'] = time.time_ns() - int(self.rt[id]['interval']*.95)
    
    # real time task to set new interval
    def p_RTSetNewInterval(self,id:str,interval:int):
        if id in self.rt:
          if self.rt[id]['interval'] != interval:
            self.rt[id]['interval'] = interval



    # initialize neo display labels
    def neoInit(self):
        self._msg_conf = [
            ('x', '     '        , X_ARROW_COLOR   ,  150,  35,  3, 126    ,1, ALIGN_RIGHT), #9*14
            ('y', '     '        , Y_ARROW_COLOR   ,  150, 115,  3, 126    ,1, ALIGN_RIGHT),
            ('z', '     '        , Z_ARROW_COLOR   ,  150, 195,  3, 126    ,1, ALIGN_RIGHT),
            ('cmd', '     '      , 'white'         ,    0, 260,  2, 308    ,1, ALIGN_LEFT),  #14*22
            ('state', '     '    , 'white'         ,  190,  10,  2, 310-190,1, ALIGN_LEFT),
            #('icon', 'grbl'      , ICON_COLOR,    0,   0, 2, 100    ,1),
            ('term', 'F1 - Help' , 'white',             0,  40,  2, 140          ,5, ALIGN_LEFT),
            ('<', '<<'          ,  'yellow'        ,   40, 380,  3, 60     ,1, ALIGN_LEFT),
            ('icon', self._ui_modes[self._ui_mode] , ICON_COLOR, 40+3*14,  385, 2, 220-40-3*14    ,1, ALIGN_CENTER),
            ('>', '>>'          ,  'lblue'         ,  220, 380,  3, 60     ,1, ALIGN_LEFT),
            ('info', 'info'      , 'white'         ,    0, 280,  2, 306    ,3, ALIGN_LEFT)  #6*51
        ]        



        self.labels = {}  # dictionary of configured messages_labels
        self.help = [
           '^r reboot',
           '^c cancel',
           '# MPG',
           '^ unlock',
           'esc cancel',
           'f2 Dxy',
           'f3 Dz',
           'f4 feed',
           '^up hist',
           '^down hist',
           '^PgUp scr',
           '^PgDn scr',
           '^left scr',
           '^right scr',
           '^home scr',


           '~ start',
           '! feed',
           '? query'
        ]     
        # wriNowrap = CWriter(self.neo, fixed, verbose=self.debug)
        # wriNowrap.set_clip(False, False, False) #row_clip=None, col_clip=None, wrap=None
        # wriNowrapArial = CWriter(self.neo, arial10, verbose=self.debug)
        # wriNowrapArial.set_clip(False, False, False) #row_clip=None, col_clip=None, wrap=None
        
        # writer = CWriter(self.neo, fixed, verbose=self.debug)
        # writer.set_clip(False, False, True) #row_clip=None, col_clip=None, wrap=None
        
        for c1 in self._msg_conf:
            (name, textline, color, x, y, scale, width, nlines,align ) = c1  # unpack tuple into five var names
            color = color2rgb(color)
            fnt=arial35 if scale==3 else (arial10 if scale==1 else fixed)
            writer = CWriter(self.neo, fnt, verbose=self.debug)
            writer.set_clip(False, False, False) #row_clip=None, col_clip=None, wrap=None


            if name in ('xyz'):
              self.neo.rect(x+5,y+5,10,10,VFD_WHITE,True)
              flw=writer.stringlen(name.upper()+': ')
              fl=Label(writer, y, x, flw,fgcolor=color)
              fl.value(name.upper()+': ',fgcolor=color)
              ll=Label(writer, y, x+flw, writer.stringlen('-999.99'), bdcolor=None, align=align)
              ll.value('{:6.2f}'.format(-123.01), fgcolor=VFD_WHITE)
              
              self.labels[name] = NeoLabelObj(text  = textline, color=VFD_WHITE , align=align, scale=scale,x=x,y=y,label=ll,fldLabel=fl, oneWidth=writer.stringlen('0'))
            elif name in ('state'):
              ll=Label(writer, y, x, width,fgcolor=color,bgcolor=VFD_BG, align=align)
              if textline.strip()!='':
                  ll.value(textline,fgcolor=color, align=align)
              else:    
                ll.value(name,fgcolor=color, align=align)
              self.labels[name] = NeoLabelObj(text  = textline, color=color , align=align , scale=scale,x=x,y=y,label=ll,oneWidth=writer.stringlen('0'))
            elif name in ('cmd','icon'):
              ll=Label(writer, y, x, width,fgcolor=color,bgcolor=VFD_BG, align=align)
              if textline.strip()!='':
                  ll.value(textline,fgcolor=color, align=align)
              else:    
                ll.value(name, align=align)
              self.labels[name] = NeoLabelObj(text  = textline, color=color , align=align , scale=scale,x=x,y=y,label=ll,oneWidth=writer.stringlen('0'))
            elif name in ('info','term'):
              ll=Textbox(writer, clip=False, row=y, col=x, width=width, nlines=nlines, bdcolor=False, fgcolor=color,bgcolor=VFD_BG)
              if textline.strip()!='':
                  ll.append(textline)
              self.labels[name] = NeoLabelObj(text  = textline, color=color , align=align , scale=scale,x=x,y=y,nlines=nlines,label=ll,oneWidth=writer.stringlen('0'))
            else: # etc
              ll=Label(writer, y, x, width,fgcolor=color,bgcolor=VFD_BG, align=align)
              if textline.strip()!='':
                  ll.value(textline,fgcolor=color, align=align)
              else:    
                ll.value(name,fgcolor=color, align=align)
              self.labels[name] = NeoLabelObj(text  = textline, color=color , align=align , scale=scale,x=x,y=y,label=ll,oneWidth=writer.stringlen('0'))
       
        self.neo_refresh= True

    # ui terminal line position decrease
    def decTermLinePos(self):
       if len(self.grbl_info)>0 and self.term_line_from>3:
          self.term_line_from -= 3

    # ui terminal position decrease
    def decTermPos(self):
       if len(self.grbl_info)>0 and self.term_pos_from>4:
          self.term_pos_from -= 5


    # ui terminal line position increase
    def incTermLinePos(self):
        if len(self.grbl_info)>0:
          lines = self.grbl_info.count('\n')  
          lines += 1
          if self.term_line_from<lines:
             self.term_line_from += 3

    # ui terminal position increase
    def incTermPos(self):
        if len(self.grbl_info)>0:
          if self.term_pos_from<50:
             self.term_pos_from += 5

    # ui terminal position home
    def homeTermPos(self):
        if len(self.grbl_info)>0:
           self.term_pos_from = 0
           self.term_line_from = 1

    # ui terminal text splitter for terminal window
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
    
    # ui info text splitter for terminal window
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
            #if len1+len(cc)>50:
            #if len1+len(cc)>50:
            #    textF +='\n'
            #    len1 =0
            len1 += len(cc)+1
            textF +='|'+cc
      return textF

    def neoPressedDraw(self):
        if self._pressedX is not None and self._pressedY is not None:
            if self._pressedOldX is not None and self._pressedOldY is not None:
                self.neo.rect(self._pressedOldX-5,self._pressedOldY-5,10,10,VFD_BG,True)
            self.neo.rect(self._pressedX-5,self._pressedY-5,10,10,VFD0_WHITE,True)
            self.neo_refresh= True

    # draw/update neo display label    
    def neoDraw(self,id):
        if id is not None:
            if DEBUG:
                print('neoDraw['+id+']',self.labels[id].x,self.labels[id].y,self.labels[id].color,self.labels[id].text)
            if isinstance(self.labels[id].label,Textbox )  :
              self.labels[id].label.clear()
              self.labels[id].label.fgcolor=self.labels[id].color
              # self.labels[id].label.append(self.labels[id].text)
              self.labels[id].label.append(self.labels[id].text[ : self.labels[id].chars])
              
              self.labels[id].label.goto(0)
            else:   
              if self.labels[id].charsl-len(self.labels[id].text)>0  and (self.labels[id].align is None or self.labels[id].align==ALIGN_LEFT) :
                  self.labels[id].label.value( self.labels[id].text + ( " " * (self.labels[id].charsl + (1 if id not in('xyz') else 0)  - len(self.labels[id].text) ))   ,fgcolor=self.labels[id].color, align=self.labels[id].align)
              else:    
                self.labels[id].label.value(self.labels[id].text[:self.labels[id].charsl],fgcolor=self.labels[id].color, align=self.labels[id].align)
            
            self.neo_refresh= True
            
            
    # ui label`s updater
    def neoLabel(self,text,id='info',color=None):
        
        color = color2rgb(color)
        l_id=id
        if id=='x':
          self.labels[id].text = '{0:.2f}'.format(self._mX)
        elif id=='y': 
          self.labels[id].text = '{0:.2f}'.format(self._mY)  
        elif id=='z':
          self.labels[id].text = '{0:.2f}'.format(self._mZ)  
        elif id=='cmd':
          self.labels[id].text = text
          if color is None:
             self.labels[id].color=VFD_YELLOW
        elif id=='state':
          self.labels[id].text = text+(' MPG' if self._mpg else '')
          if color is None and text.lower().startswith('alarm'):
             self.labels[id].color=VFD_RED
          elif color is None and (text.lower().startswith('run') or text.lower().startswith('jog')):
             self.labels[id].color=VFD_GREEN
          elif color is None:
             self.labels[id].color=VFD_WHITE
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
          self.labels[id].text = text
          if color is None:
             self.labels[id].color=VFD_GREEN
          else:   
             self.labels[id].color=color
        elif id=='info':
          self.labels[id].text = text
          if color is None:
             self.labels[id].color=VFD_LBLUE if self._mpg  else VFD_WHITE
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
        self.neoLabel(text,id='icon',color=color2rgb(ICON_COLOR) if color is None else  color)

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
      if command.startswith('$J=') :
        self._grblExecProgress='do'  
      elif not( command.startswith('?') or command.startswith('!') or command.startswith('$') ):
        self._grblExecProgress='do'  
      self.uart_grbl_mpg.write(command.encode())

      if not command.startswith('?'):
          self.query_now('mpgCommand')
          self.sendedQuery2grblCounter = 0

    #jog $J=G91 X0 Y-5 F600
    #$J=G91 X1 F100000

    def grblJog(self, x:float=0.0, y: float=0.0, z:float=0.0, feedrate:float=None):
      if feedrate is None:
         f=self.feedrate
      else:
         f=feedrate   
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
          # self.query_now('grblJog') that is not needed, jog command returns status itself
          self.p_RTSetNewInterval('autoQuery2grbl',GRBL_QUERY_INTERVAL_RUN)
          # if self.timeDelta2query != GRBL_QUERY_INTERVAL_RUN:
          #     self.timeDelta2query = GRBL_QUERY_INTERVAL_RUN
          # if self.time2query > time.time_ns()+self.timeDelta2query:
          #     self.time2query = time.time_ns()+self.timeDelta2query
          
          self.neoDisplayJog() 
    
    def toggleMPG(self):
        self.neoLabel("#",id='cmd')
        #self.uart_grbl_mpg.write(bytearray(b'\x8b\r\n'))
        self.uart_grbl_mpg.write(bytearray(b'\x8b'))
        self.query_now('toggleMPG')

    def query4MPG(self):
        #print('point2/0',self._query4MPG_countDown,self._mpg, self.MPG_time2query , time.time_ns(),self.MPG_time2query > time.time_ns()+MPG_INTERVAL)
        # if (self._mpg is None or self._mpg==0) and self._query4MPG_countDown>0 and self.MPG_time2query < time.time_ns()+MPG_INTERVAL:
        if (self._mpg is None or self._mpg==0) and self._query4MPG_countDown>0 :
           #  self.MPG_time2query=time.time_ns()
           self._query4MPG_countDown -= 1
           self.toggleMPG()
           

    


    def send2grblOne(self,command:str):
      if DEBUG or (command is not None and command!='' and not command.startswith('?')) :
        print('send2grblOne:',command,len(command))
      if command in ('~','!','?'):
        #self.flashKbdLEDs(LED_ALL , BLINK_2) ##7 - 3 leds       # 1 - macro1
        self.mpgCommand(command)
        if command !='?':
          self.sendedQuery2grblCounter = 0
          self.neoLabel(command,id='cmd')
        else:
          if self.editCmd!='':
            self.grblCmd2send=[]
          else: 
             self.sendedQuery2grblCounter+=1
             if  self.sendedQuery2grblCounter>10:
                self.sendedQuery2grblCounter = 0
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
          self.grblJog(z=-self.stepdZ) 
      elif  command=='+z':
          self.grblJog(z=self.stepdZ)
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
          self.neoLabel(self.getHelp(),id='term')
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
                self._grblExecProgress='do'
                self.p_RTSetNewInterval('popCmd2grbl',GRBL_QUERY_INTERVAL_RUN)

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
      if self._grblExecProgress!='do':
          self.popCmd2grbl()

    def popCmd2grbl(self):
      if len(self.grblCmd2send)>0:
        l_cmd=self.grblCmd2send[0]
        if self._grblExecProgress == 'do' and (
          l_cmd=='-y' or l_cmd=='+y' or 
          l_cmd=='-x' or l_cmd=='+x' or 
          l_cmd=='-z' or l_cmd=='+z' ):
          print('popCmd2grbl: busy', self._grblExecProgress, l_cmd )
          return
        else:
          l_cmd=self.grblCmd2send.pop(0)
          self.send2grblOne(l_cmd)

    def autoQuery2grbl(self):
        # self.gotQuery=True
        self.send2grblOne('?') # get status from grbl cnc machine          

    def query_now(self, parent):
        if self.debug:
            print('query_now',parent)
        #self._need_query = True    
        # self.gotQuery = False
        self.p_RTSetRunNow('autoQuery2grbl')


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
    
    
       
    # @property
    # def need_query(self):
    #     # l_nq = self._need_query or time.time_ns()-self.start_time_q>GRBL_QUERY_INTERVAL
    #     #l_nq = self._need_query or time.time_ns()>self.time2query
    #     l_nq = self._need_query or (time.time_ns()>self.time2query)
    #     #print('l_nq=',l_nq,self.time2query > time.time_ns(),self.time2query , time.time_ns())
    #     if l_nq:
    #       if self.gotQuery:
    #           if time.time_ns()>self.time2query:
    #               self.time2query = time.time_ns()+self.timeDelta2query
    #           self.gotQuery=False
    #           self._need_query = False
    #     return l_nq


    @property
    def step(self):
        return self._dXY          

    @property
    def stepdZ(self):
        return self._dZ          

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
    def parseStateOne(self,lineStateIn:str):
      try:
        ii=0
        token =''
        if lineStateIn is None:
          self._parse_state_code='empty'
          return
        lineStateIn=lineStateIn.strip()
           


        #print('grblState IN ',grblState,']]]]]]]]]]]]]',grblState.find('error:'))  
        #grblState=grblState.replace('ok','').replace('\n','').replace('\r','')
        self._parse_state_code='parse'
        if lineStateIn.startswith('ok'):
          #print('OKKor',lineStateIn,']]]]]]]]]]]]]','prev:', self._grblExecProgress)  
          if self._grblExecProgress=='do':
             self._grblExecProgress='doing'
          elif self._grblExecProgress=='doing':
             pass
          else:  
            self._grblExecProgress='ok'
          self.changeState('ok')
          self._parse_state_code='done'
          return        
        elif lineStateIn.startswith('alarm:'):
          print('ALarm',lineStateIn,']]]]]]]]]]]]]')  
          self._grblExecProgress='alarm'
          self.changeState('alarm')
          self._parse_state_code='done'
          return  
        elif lineStateIn.startswith('error:'):
          print('ERRor',lineStateIn,']]]]]]]]]]]]]')  
          self._grblExecProgress='error'
          self.changeState('error')
          self._parse_state_code='done'
          return          
        # general purpose state parsing      
        elif lineStateIn.find('<')>=0 and lineStateIn.find('>')>=0 and  lineStateIn.find('<')<lineStateIn.find('>')>=0 :
            self.grbl_display_state = lineStateIn[lineStateIn.find('<'):lineStateIn.find('>')+1]

            l_state = None 

            for ii,token in enumerate(self.grbl_display_state[1:-1].lower().split('|')):
                if ii==0 : # state the first token
                  l_state = token
                else:
                    elem = token.split(':')
                    if len(elem)>1 and elem[0]=='mpg' and elem[1] is not None and (elem[1]=='1' or elem[1]=='0'):
                        self._mpg_prev=self._mpg
                        self._mpg=(elem[1]=='1')
                        self.labels['info'].color=VFD_LBLUE if self._mpg  else VFD_WHITE
                        if self._mpg==1:
                            self._query4MPG_countDown = 0
                        
                    elif  len(elem)>1 and elem[0]=='mpos' and elem[1] is not None:       
                        self.changeMpos(elem[1].split(','))
                    elif  len(elem)>1 and elem[0]=='WCO' and elem[1] is not None:       
                        self.changeWCO(elem[1].split(','))    
            if l_state is not None:
                 self.changeState(l_state)            
            self._parse_state_code='done'
            return
        
        elif lineStateIn.find('[')>=0 and lineStateIn.find(']')>=0 and  lineStateIn.find('[')<lineStateIn.find(']')>=0 :
            lineStateIn=lineStateIn[lineStateIn.find('['):lineStateIn.find('[')+1]
            self.grbl_info=lineStateIn
            if lineStateIn.count('Unlocked')>0:
              self.changeState('unlocked')
              self._grblExecProgress='done'
            self._parse_state_code='done'  
            return
        elif  lineStateIn.startswith('$')  :
          self.grbl_info=lineStateIn           
          self._parse_state_code='done'
          return
        else:
          l_cntNewL=lineStateIn.count('\n')
          if l_cntNewL>0:
              if lineStateIn.count('ok')>0:
                  self._grblExecProgress='ok'
          self._parse_state_code='done'
          return
        
            
              

 
        
        



      except:
          print('error parseState ',lineStateIn, ii, token)
          self._parse_state_code='fail'  

    def parseState(self, stateIn:str):
      for item in stateIn.splitlines():
        if item.strip()!='':
          self.parseStateOne(item)

    def changeState(self,newState:str):
        prv = self._state_prev
        self._state_prev = self._state
        self._state = newState
        self._state_is_changed = (prv is None or  prv != self._state)     
        self._state_time_change = time.time_ns()
        if (self._state.startswith('run') or self._state.startswith('jog')) or self._state_is_changed  :
            self.p_RTSetNewInterval('autoQuery2grbl',GRBL_QUERY_INTERVAL_RUN)
        elif not (self._state.startswith('run') or self._state.startswith('jog')) :
            self.p_RTSetNewInterval('autoQuery2grbl',GRBL_QUERY_INTERVAL_IDLE)
        if self._grblExecProgress in ('do','doing','alarm','error') and (self._state.startswith('idle') or self._state.startswith('alarm')) :
            self._grblExecProgress='done'
            # set rotary to initial
            self.initRotaryMpos()     
        self.neo_refresh= True


    def displayState(self,grblState:str):     

      self.parseState(grblState)
      # print("MPG ->",grblState,' \n - >> prev ',self.state_prev, self.mpg_prev,' now=>',self.state, self.mpg)
      self.neoLabel(self.grbl_display_state,id='info')
      
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
                  self.neoIcon('Run')
              elif self.state == 'jog':    
                  self.neoLabel(self.state,id='state')
                  self.neoDisplayJog()
                  #self.neoIcon('Jog')
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
           self.neoIcon(text=self._ui_modes[self._ui_mode])   
        else:
          self.neoIcon(text=('>>>' if self._jog_arrow.startswith('+') else '<<<') +
                       ''+(' {0:.1f}'.format(self._dZ) if self._jog_arrow.endswith('z') else ' {0:.1f}'.format(self._dXY))
                       #+'f={0:.0f}'.format(self._feedrate)
                       ,color=color)   



    def setEdit(self, text):
       self.editCmd=text

    def neoShowEdit(self):
      self.sendedQuery2grblCounter = 0
      # self.neoIdle()
      self.neoLabel(text=self.editCmd,id='cmd')
      

    def procUartInByte(self,chars):
      # Process the bytes (e.g., print its integer value or character)
      if len(chars)>0:
            if self.debug:
                print(chars.decode())
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
    

    
    
    # event when grbl pos changed
    def changeMpos(self, xyz):
      if len(xyz)==3:
        self._mX_prev, self._mY_prev,self._mZ_prev = (self._mX, self._mY,self._mZ)
        self._mX, self._mY,self._mZ = [ float(xx) for xx in xyz ]
        self._mPosInited:bool = True
      elif len(xyz)==4:
        self._mX_prev, self._mY_prev,self._mZ_prev,self._mA_prev = (self._mX, self._mY,self._mZ,self._mA)
        self._mX, self._mY,self._mZ,self._mA = [ float(xx) for xx in xyz ]  
        self._mPosInited:bool = True
      elif len(xyz)==5:
        self._mX_prev, self._mY_prev,self._mZ_prev,self._mA_prev,self._mB_prev = (self._mX, self._mY,self._mZ,self._mA,self._mB)
        self._mX, self._mY,self._mZ,self._mA,self._mB = [ float(xx) for xx in xyz ]  
        self._mPosInited:bool = True
      elif len(xyz)==6:
        self._mX_prev, self._mY_prev,self._mZ_prev,self._mA_prev,self._mB_prev,self._mC_prev = (self._mX, self._mY,self._mZ,self._mA,self._mB,self._mC)
        self._mX, self._mY,self._mZ,self._mA,self._mB,self._mC = [ float(xx) for xx in xyz ]  
        self._mPosInited:bool = True

      self._mpos_changed = (self._mX_prev != self._mX or self._mY_prev != self._mY or self._mZ_prev != self._mZ)
      if self._mpos_changed:
         #print('changeMpos:')
         self.initRotaryMpos()
         self.neo_refresh= True



 
    # event when grbl pos changed
    def changeWCO(self, xyz):
      if len(xyz)==3:
        self._wX_prev, self._wY_prev,self._wZ_prev = (self._wX, self._wY,self._wZ)
        self._wX, self._wY,self._wZ = [ float(xx) for xx in xyz ]
        self._wpos_changed = True
      elif len(xyz)==4:
        self._wX_prev, self._wY_prev,self._wZ_prev,self._wA_prev = (self._wX, self._wY,self._wZ,self._wA)
        self._wX, self._wY,self._wZ,self._wA = [ float(xx) for xx in xyz ]  
        self._wpos_changed = True
      elif len(xyz)==5:
        self._wX_prev, self._wY_prev,self._wZ_prev,self._wA_prev,self._wB_prev = (self._wX, self._wY,self._wZ,self._wA,self._wB)
        self._wX, self._wY,self._wZ,self._wA,self._wB = [ float(xx) for xx in xyz ]  
        self._wpos_changed = True
      elif len(xyz)==6:
        self._wX_prev, self._wY_prev,self._wZ_prev,self._wA_prev,self._wB_prev,self._wC_prev = (self._wX, self._wY,self._wZ,self._wA,self._wB,self._wC)
        self._wX, self._wY,self._wZ,self._wA,self._wB,self._wC = [ float(xx) for xx in xyz ]  
        self._wpos_changed = True

      self._wpos_changed = (self._wX_prev != self._wX or self._wY_prev != self._wY or self._wZ_prev != self._wZ)
      if self._wpos_changed:
         print('changeWpos:', self._wX, self._wY, self._wZ)
         self.neo_refresh= True

    def initRotaryMpos(self):
        if self._mPosInited: # set rotary mpos only at first time 
          for rotObj  in self.rotaryObj:  
            if rotObj['obj'] is not None:
                rotObj['mpos'] = (self._mX if rotObj['axe']=='x' else ( self._mY if rotObj['axe']=='y' else self._mZ ))
                rotObj['rotary_on_mpos'] = rotObj['obj'].value()
                rotObj['value_prev'] = rotObj['obj'].value()
                rotObj['value'] = rotObj['obj'].value()
                rotObj['nanosec'] = time.time_ns()
                rotObj['nanosec_prev'] = rotObj['nanosec']
        
    # link with rotary encoder  object
    def set_rotary_obj(self,rotaryObj,rotN,axe,unit):
        self.rotaryObj[rotN]={'obj':rotaryObj ,'axe':axe,'unit':unit, 
                              'state':self.state,
                              'value':rotaryObj.value(),
                              'value_prev':rotaryObj.value(),
                              'mpos':self._mX if axe=='x' else ( self._mY if axe=='y' else self._mZ ),
                              'nanosec':time.time_ns(), 
                              'nanosec_prev':time.time_ns(), 
                              'rotary_on_mpos':None,
                              'scale':1.0
                                }



    def rotary_listener(self,rotN):
        if self.rotaryObj[rotN]['obj'] is not None:
            self.rotaryObj[rotN]['value_prev']=self.rotaryObj[rotN]['value']
            self.rotaryObj[rotN]['value']=self.rotaryObj[rotN]['obj'].value()
            self.rotaryObj[rotN]['nanosec_prev']=self.rotaryObj[rotN]['nanosec']
            self.rotaryObj[rotN]['nanosec']=time.time_ns()
            # if self._mPosInited:
            # if self.rotaryObj[rotN]['nanosec_prev']-self.rotaryObj[rotN]['nanosec']>1000000: #
                    # self.rotaryObj[rotN]['rotary_on_mpos']=self.rotaryObj[rotN]['value']
                # print ('rotary_listener: #',rotN,self.rotaryObj[rotN]['axe'],self.rotaryObj[rotN]['value'],self.rotaryObj[rotN]['mpos'])
                # print ('              delta:', self.rotaryObj[rotN]['value']- self.rotaryObj[rotN]['rotary_on_mpos']  )


    # callback for rotary 0 (x)
    def rotary_listener0(self):
        self.rotary_listener(0)
        
    # callback for rotary 1 (y)    
    def rotary_listener1(self):
        self.rotary_listener(1)

    # task every 1s
    def upd_rotary(self):
        if self._grblExecProgress in ('do','doing','alarm','error'):
            return
        for rotN in range(len(self.rotaryObj)):
            if self.rotaryObj[rotN]['obj'] is not None:
                if self._mPosInited and self.rotaryObj[rotN]['state'] not in ('jog','run','planed'):
                    delta_val = self.rotaryObj[rotN]['value'] - self.rotaryObj[rotN]['rotary_on_mpos']
                    delta_time = self.rotaryObj[rotN]['nanosec'] - self.rotaryObj[rotN]['nanosec_prev']
                    if delta_val==0 or time.time_ns()-self.rotaryObj[rotN]['nanosec'] < PENDANT_READ_INTERVAL:
                       #print('upd_rotary: no timeout no movement, skip', rotN, delta_time)
                       continue
                    if delta_time>0:
                        speed = abs(delta_val) / (delta_time / 1_000_000_000)  # units per second
                    else:
                        speed = 0


                    # self.rotaryObj[rotN]['scale']=scale
                    #scale = self.rotaryObj[rotN]['scale']
                    step = delta_val * self.rotaryObj[rotN]['unit'] *  self.rotaryObj[rotN]['scale']
                    feed = 100.0
                    if abs(delta_val)>80:
                        feed = 10000.0
                    elif abs(delta_val)>50:
                        feed = 500.0
                    elif abs(delta_val)>10:
                       feed = 200.0

                        
                    # print ('upd_rotary:', rotN, self.rotaryObj[rotN]['axe'], ' feed=', feed, ' speed=',  speed)   

                    if self.rotaryObj[rotN]['axe']=='x':
                        self.grblJog(x=step, feedrate=feed)
                    elif self.rotaryObj[rotN]['axe']=='y':
                        self.grblJog(y=step, feedrate=feed)
                    elif self.rotaryObj[rotN]['axe']=='z':
                        self.grblJog(z=step, feedrate=feed)

    def touchscreen_press(self,x, y):
        # print('touchscreen_press:',x,y)  
        self._pressedArea=''
        self._pressedOldX = self._pressedX
        self._pressedOldY = self._pressedY  
        self._pressedX = x
        self._pressedY = y
        self.neoPressedDraw()
        

        for label in self.labels:
            if label in ('x','y','z','<','>'):
               ll=self.labels[label]
               if x>=ll.x-2 and x<=ll.x+ll.width+2 and y>=ll.y-2 and y<=ll.y+ll.height+2:
                   self._pressedArea=label
                   break
        if self._pressedArea!='':       
          print('  pressed ',self._pressedArea)
          if self._pressedArea in ('<','>'):
             self.nextUiMode(-1 if self._pressedArea in ('<') else 1)
          elif self._pressedArea in ('x','y','z'):       
            if self.labels[self._pressedArea].color!=VFD_YELLOW:
              self.labels[self._pressedArea].color=VFD_YELLOW
              self.neo_refresh =True
              if self.rotaryObj[0]['axe']!=self._pressedArea:
                  self.rotaryObj[0]['axe'] = self._pressedArea
                  self.neoLabel('',id=self._pressedArea)
                  self.initRotaryMpos()
              if self._pressedArea!='x' and self.labels['x'].color!=VFD_LBLUE:
                  self.labels['x'].color=VFD_LBLUE
                  self.neoLabel('',id='x')
              if self._pressedArea!='y' and self.labels['y'].color!=VFD_LBLUE:
                  self.labels['y'].color=VFD_LBLUE
                  self.neoLabel('',id='y')
              if self._pressedArea!='z' and self.labels['z'].color!=VFD_LBLUE:
                  self.labels['z'].color=VFD_LBLUE
                  self.neoLabel('',id='z')

    def nextUiMode(self, direction):
        self._ui_mode+=direction
        if direction==0: # enter in confirm mode
          self._ui_mode_prev=self._ui_mode
          self._ui_mode = len(self._ui_modes)-1 # 'confirm' mode, last element    
        elif self._ui_mode<0:
          self._ui_mode=len(self._ui_modes)-1
        elif self._ui_mode>=len(self._ui_modes)-1 or self._ui_modes[self._ui_mode]=='confirm':
          self._ui_mode=0

        self._ui_confirm='unkn'
        self.neoIcon(text=self._ui_modes[self._ui_mode])   

    def enterConfirmMode(self):
       self.nextUiMode(0)


    def getConfirm(self):
       answ=self._ui_confirm
       self._ui_confirm='unkn'
       return answ

          
       


    def button_red_callback(self,pin,button): # right key
        print('button_red_callback')
        if self._ui_modes[self._ui_mode] == 'confirm':
          self._ui_confirm='no'
          self._ui_mode= self._ui_mode_prev
        else:
          self.nextUiMode(1) 
           
             

    def button_red_callback_long(self,pin,button):
        print('button_red_callback_long')
 
    def button_yellow_callback(self,pin,button):
        print('button_yellow_callback')
        if self._ui_modes[self._ui_mode] == 'confirm':
          self._ui_confirm='yes'
          self._ui_mode= self._ui_mode_prev
        else:
          self.nextUiMode(-1) 


    def button_yellow_callback_long(self,pin ,button):
        print('button_yellow_callback_long')

