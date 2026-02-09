import time
import machine

from machine import UART
from gui import Gui, VFD_YELLOW, VFD_LBLUE,VFD_WHITE

 

BLINK_2 = 1
BLINK_5 = 2
BLINK_INFINITE = 3
NOBLINK = 4
 

DEBUG= False








#GRBL_QUERY_INTERVAL = 0.5
#GRBL_QUERY_INTERVAL_IDLE = 10
GRBL_QUERY_INTERVAL_IDLE = 10000000000  # 10s in nanoseconds
GRBL_QUERY_INTERVAL_RUN = 500000000  # 0.5s in nanoseconds
MPG_INTERVAL = 500000000  # 0.5s in nanoseconds
ROTARY_DUMP2_JOG_INTERVAL = 600000000  # 0.6s in nanoseconds
POP_CMD_GRBL_INTERVAL =  200000000 # 0.2s in nanoseconds for pop cmd to grbl
RUN_NOW_INTERVAL =  200000000 # 0.2s in nanoseconds for pop cmd to grbl



MAX_BUFFER_SIZE = 200



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
                  

        
        


        


        

class GrblState(object):
    __version__ = '0.1'
    rt={} # real time tasks

    helpIdx=-1
    grblParams={
      '_mX': 0.0,
      '_mY': 0.0,
      '_mZ': 0.0,
      '_mA': 0.0,
      '_mB': 0.0,
      '_mC': 0.0,

      '_mX_prev': 0.0,
      '_mY_prev': 0.0,
      '_mZ_prev': 0.0,
      '_mA_prev': 0.0,
      '_mB_prev': 0.0,
      '_mC_prev': 0.0,

      '_wX': 0.0,
      '_wY': 0.0,
      '_wZ': 0.0,
      '_wA': 0.0,
      '_wB': 0.0,
      '_wC': 0.0,

      '_wX_prev': 0.0,
      '_wY_prev': 0.0,
      '_wZ_prev': 0.0,
      '_wA_prev': 0.0,
      '_wB_prev': 0.0,
      '_wC_prev': 0.0,
      
      '_mpg':   None,
      '_mpg_prev': '',
      '_wcs':  '', #Work Coordinate System (WCS)
      '_wcs_prev':  '', #Work Coordinate System (WCS)
      '_state':  'Idle',
      '_state_prev':  'unk'
    }
    
    _wpos_changed:bool  = False
    _mpos_changed:bool  = False

    _mPosInited:bool = False
    #work coordinate offset (WCO). Used to calculate WPos from MPos 

    _wcs_changed:bool = False
    neo = None
    

    debug:bool = DEBUG 
    _error:str = ''
    _alarm:str = ''
    

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




    
    uartInNewData:int = -1
    bufferUartIn=['','','',''] #
    bufferUartPos:int = 0
    bufferUartPrev:int = 0
 

    
    # statetext:str = ''
    # prev_statetext:str  = ''
    grblCmd2send=[]
    grblCmdHist=[]
    grblCmd2HistPos:int = 0






    


    
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
        self.gui=Gui(neo=self.neo, grblParams=self.grblParams,grblParserObj=self, debug=self.debug)
        

        
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


    
    def toggleMPG(self):
        self.gui.neoLabel("#",id='cmd')
        #self.uart_grbl_mpg.write(bytearray(b'\x8b\r\n'))
        self.uart_grbl_mpg.write(bytearray(b'\x8b'))
        self.query_now('toggleMPG')

    def query4MPG(self):
        #print('point2/0',self._query4MPG_countDown,self.grblParams['_mpg'], self.MPG_time2query , time.time_ns(),self.MPG_time2query > time.time_ns()+MPG_INTERVAL)
        # if (self.grblParams['_mpg'] is None or self.grblParams['_mpg']==0) and self._query4MPG_countDown>0 and self.MPG_time2query < time.time_ns()+MPG_INTERVAL:
        if (self.grblParams['_mpg'] is None or self.grblParams['_mpg']==0) and self._query4MPG_countDown>0 :
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
          self.gui.neoLabel(command,id='cmd')
        else:
          if self.editCmd!='':
            self.grblCmd2send=[]
          else: 
             self.sendedQuery2grblCounter+=1
             if  self.sendedQuery2grblCounter>10:
                self.sendedQuery2grblCounter = 0
                self.gui.neoLabel('',id='cmd')
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
          self.dec_feedrateJog()
          self.gui.neoIcon('feed {0:.0f}'.format(self._feedrateJog))
      elif command=='+feed':
          self.inc_feedrateJog()
          self.gui.neoIcon('feed {0:.0f}'.format(self._feedrateJog))
      elif command=='-stepXY' :    
          self.dec_stepXY()
          if self._dXY<1:
            self.gui.neoIcon('dX {0:.1f}'.format(self._dXY).replace('.',','))
          else:  
             self.gui.neoIcon('dX {0:.0f}'.format(self._dXY))
      elif command=='+stepXY' :    
          self.inc_stepXY()
          if self._dXY<1:
            self.gui.neoIcon('dX {0:.1f}'.format(self._dXY).replace('.',','))
          else:  
             self.gui.neoIcon('dX {0:.0f}'.format(self._dXY))
      elif command=='-stepZ' :    
          self.dec_stepZ()
          if self._dZ<1:
            self.gui.neoIcon('dZ {0:.1f}'.format(self._dZ).replace('.',','))
          else:  
             self.gui.neoIcon('dZ {0:.0f}'.format(self._dZ))
      elif command=='+stepZ' :    
          self.inc_stepZ()
          if self._dZ<1:
            self.gui.neoIcon('dZ {0:.1f}'.format(self._dZ).replace('.',','))
          else:  
             self.gui.neoIcon('dZ {0:.0f}'.format(self._dZ))
      elif command=='stepXY' :    
          self.stepXY()
          self.gui.neoIcon('dXY\n{0:.1f}'.format(self._dXY))
      elif command=='stepZ' :    
          self.stepZ()
          self.gui.neoIcon('dZ\n{0:.1f}'.format(self._dZ))
      elif command=='feed' : 
          self.set_feedrate()
          self.gui.neoIcon('feed\n{0:.0f}'.format(self._feedrateJog))
      elif command=='termLineUp' : 
          self.decTermLinePos()
          if len(self.grbl_info)>0:
            self.gui.neoTerm(self.grbl_info)
      elif command=='termLineDown' : 
          self.incTermLinePos()
          if len(self.grbl_info)>0:
            self.gui.neoTerm(self.grbl_info) 
      elif command=='termLineLeft' : 
          self.decTermPos()
          if len(self.grbl_info)>0:
            self.gui.neoTerm(self.grbl_info)
      elif command=='termLineRight' : 
          self.incTermPos()
          if len(self.grbl_info)>0:
            self.gui.neoTerm(self.grbl_info)           
      elif command=='termHome' : 
          self.homeTermPos()
          if len(self.grbl_info)>0:
            self.gui.neoTerm(self.grbl_info)   
      elif command in ('#'):  
        self.toggleMPG()
      elif command in ('cancel'):  
        # if self.state == 'run' or self.state == 'jog':
          #self.flashKbdLEDs(LED_SCROLLLOCK , BLINK_5) ##2 - leds ???       # 2 - macro1 10/2 blink
          self.uart_grbl_mpg.write(bytearray(b'\x85\r\n')) #Jog Cancel
          self.uart_grbl_mpg.write(bytearray(b'\x18\r\n')) # cancel ascii ctrl-x
          self.gui.neoLabel(command,id='cmd')
          self.query_now('cancel')
        # else:
          #self.flashKbdLEDs(LED_ALL , BLINK_2) ##7 - 3 leds       # 1 - macro1
          # pass 
      elif command in ('reset'):  
          self.uart_grbl_mpg.write(bytearray(b'\x85\r\n')) #Jog Cancel
          self.uart_grbl_mpg.write(bytearray(b'\x18\r\n')) # cancel ascii ctrl-x
          self.gui.neoLabel(command,id='cmd')
          self.query_now('reset')
          machine.soft_reset()
      elif command in ('help'):  
          self.gui.neoLabel(self.getHelp(),id='term')
      elif command in ('^'):  
        #self.flashKbdLEDs(LED_ALL , BLINK_2) ##7 - 3 leds       # 1 - macro1
        self.gui.neoLabel('$X',id='cmd')
        self.uart_grbl_mpg.write('$X'.encode()+b'\r\n')
        self.query_now('$X')
      else:
        if command.strip()!='':
            # self.neoInfo(command[:10],virtual_width = 128)
            self.gui.neoLabel(command,id='cmd')
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
            self.gui.neoLabel(self.editCmd,id='cmd')
  

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
        return self.gui._feedrateJog  
    
    @property
    def editCmd(self):
        return self.gui._editCmd

    
    
       
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
        return self.grblParams['_mpg']    
    
    @property
    def mpg_prev(self):
        return self.grblParams['_mpg_prev']
    
    @property
    def state(self):
        return self.grblParams['_state']  
    
    @property
    def state_prev(self):
        return self.grblParams['_state_prev']     
    
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
                        self.grblParams['_mpg_prev']=self.grblParams['_mpg']
                        self.grblParams['_mpg']=(elem[1]=='1')
                        self.gui.labels['info'].color=VFD_LBLUE if self.grblParams['_mpg']  else VFD_WHITE
                        if self.grblParams['_mpg']==1:
                            self._query4MPG_countDown = 0
                        
                    elif  len(elem)>1 and elem[0]=='mpos' and elem[1] is not None:       
                        self.changeMpos(elem[1].split(','))
                    elif  len(elem)>1 and elem[0]=='WCO' and elem[1] is not None:       
                        self.changeWCO(elem[1].split(','))
                    elif  len(elem)>=1 and elem[0]=='WCS' and elem[1] is not None:       
                        self.changeWCS(elem[1])                            
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
        prv = self.grblParams['_state_prev']
        self.grblParams['_state_prev'] = self.grblParams['_state']
        self.grblParams['_state'] = newState
        self._state_is_changed = (prv is None or  prv != self.grblParams['_state'])     
        self._state_time_change = time.time_ns()
        if (self.grblParams['_state'].startswith('run') or self.grblParams['_state'].startswith('jog')) or self._state_is_changed  :
            self.p_RTSetNewInterval('autoQuery2grbl',GRBL_QUERY_INTERVAL_RUN)
        elif not (self.grblParams['_state'].startswith('run') or self.grblParams['_state'].startswith('jog')) :
            self.p_RTSetNewInterval('autoQuery2grbl',GRBL_QUERY_INTERVAL_IDLE)
        if self._grblExecProgress in ('do','doing','alarm','error') and (self.grblParams['_state'].startswith('idle') or self.grblParams['_state'].startswith('alarm')) :
            self._grblExecProgress='done'
            # set rotary to initial
            if self.gui._ui_modes[self.gui._ui_mode] in ( 'main', 'drive'):
              self.gui.initRotaryStart()     
        self.gui.neo_refresh= True


    def displayState(self,grblState:str):     

      self.parseState(grblState)
      # print("MPG ->",grblState,' \n - >> prev ',self.state_prev, self.mpg_prev,' now=>',self.state, self.mpg)
      self.gui.neoLabel(self.grbl_display_state,id='info')
      
      if len(self.grbl_info)>0:
         self.gui.neoTerm(self.grbl_info)
         
      self.gui.neoLabel('{0:.2f}'.format(self.grblParams['_mX']),id='x')
      self.gui.neoLabel('{0:.2f}'.format(self.grblParams['_mY']),id='y')
      self.gui.neoLabel('{0:.2f}'.format(self.grblParams['_mZ']),id='z')
      
      
      
      
      if self.mpg is not None and (self.mpg_prev is None or self.mpg !=self.mpg_prev):
          self.grblParams['_mpg_prev']=self.grblParams['_mpg']
      if self.state_is_changed() or self.state == 'idle' or self.state.startswith('hold') :  
              if self.state.startswith('alarm'):
                  self._jog_arrow = ''
                  self.gui.neoDisplayJog()
                  self.gui.neoIcon('Alarm\n^\nshft+6')
                  self.gui.neoLabel(self.state,id='state')
              elif self.state == 'run':    
                  self.gui.neoLabel(self.state,id='state')
                  self.gui.neoIcon('Run')
              elif self.state == 'jog':    
                  self.gui.neoLabel(self.state,id='state')
                  self.gui.neoDisplayJog()
                  #self.gui.neoIcon('Jog')
              elif self.state=='unlocked':
                  self.gui.neoLabel(self.state,id='state')
              elif self.state=='hold:1':
                  self.gui.neoLabel(self.state,id='state')
              elif self.state=='hold:0':
                  #self.flashKbdLEDs(LED_NUMLOCK , BLINK_5)
                  # self.neoInfo(self.state)  
                  self.gui.neoLabel(self.state,id='state')
              elif self.state.startswith('error'): 
                  self._jog_arrow = ''
                  self.gui.neoDisplayJog() 
                  # self.neoError('err')  
                  #self.flashKbdLEDs(LED_CAPSLOCK , BLINK_5) 
                  self.gui.neoLabel(self.state,id='state')
              elif self.state == 'idle' :
                  self._jog_arrow = ''
                  self.gui.neoDisplayJog()    
                  #self.flashKbdLEDs(LED_ALL , NOBLINK) 
                  # self.neoIdle()
                  self.gui.neoLabel(self.state,id='state')
    










    def neoShowEdit(self):
      self.sendedQuery2grblCounter = 0
      # self.neoIdle()
      self.gui.neoLabel(text=self.editCmd,id='cmd')
      

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
        self.grblParams['_mX_prev'], self.grblParams['_mY_prev'],self.grblParams['_mZ_prev'] = (self.grblParams['_mX'], self.grblParams['_mY'],self.grblParams['_mZ'])
        self.grblParams['_mX'], self.grblParams['_mY'],self.grblParams['_mZ'] = [ float(xx) for xx in xyz ]
        self._mPosInited:bool = True
      elif len(xyz)==4:
        self.grblParams['_mX_prev'], self.grblParams['_mY_prev'],self.grblParams['_mZ_prev'],self.grblParams['_mA_prev'] = (self.grblParams['_mX'], self.grblParams['_mY'],self.grblParams['_mZ'],self.grblParams['_mA'])
        self.grblParams['_mX'], self.grblParams['_mY'],self.grblParams['_mZ'],self.grblParams['_mA'] = [ float(xx) for xx in xyz ]  
        self._mPosInited:bool = True
      elif len(xyz)==5:
        self.grblParams['_mX_prev'], self.grblParams['_mY_prev'],self.grblParams['_mZ_prev'],self.grblParams['_mA_prev'],self.grblParams['_mB_prev'] = (self.grblParams['_mX'], self.grblParams['_mY'],self.grblParams['_mZ'],self.grblParams['_mA'],self.grblParams['_mB'])
        self.grblParams['_mX'], self.grblParams['_mY'],self.grblParams['_mZ'],self.grblParams['_mA'],self.grblParams['_mB'] = [ float(xx) for xx in xyz ]  
        self._mPosInited:bool = True
      elif len(xyz)==6:
        self.grblParams['_mX_prev'], self.grblParams['_mY_prev'],self.grblParams['_mZ_prev'],self.grblParams['_mA_prev'],self.grblParams['_mB_prev'],self.grblParams['_mC_prev'] = (self.grblParams['_mX'], self.grblParams['_mY'],self.grblParams['_mZ'],self.grblParams['_mA'],self.grblParams['_mB'],self.grblParams['_mC'])
        self.grblParams['_mX'], self.grblParams['_mY'],self.grblParams['_mZ'],self.grblParams['_mA'],self.grblParams['_mB'],self.grblParams['_mC'] = [ float(xx) for xx in xyz ]  
        self._mPosInited:bool = True

      self._mpos_changed = (self.grblParams['_mX_prev'] != self.grblParams['_mX'] or self.grblParams['_mY_prev'] != self.grblParams['_mY'] or self.grblParams['_mZ_prev'] != self.grblParams['_mZ'])
      if self._mpos_changed:
         #print('changeMpos:')
         if self.gui._ui_modes[self.gui._ui_mode] in ( 'main', 'drive'):
              self.gui.initRotaryStart()
         self.gui.neo_refresh= True



 
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
         self.gui.neo_refresh= True


    def changeWCS(self, wcs):
      self._wcs_prev = self._wcs
      self._wcs = wcs
      self._wcs_changed = (self._wcs_prev != self._wcs)
      if self._wcs_changed:
         print('changeWCS:', self._wcs)
         self.gui.neo_refresh= True

    # callback for rotary 0 (x)
    def rotary_listener0(self):
        self.gui.rotary_listener(0)
        
    # callback for rotary 1 (y)    
    def rotary_listener1(self):
        self.gui.rotary_listener(1)


    # task every 1s
    def upd_rotary(self):
        if self._grblExecProgress in ('do','doing','alarm','error'):
            #print ('upd_rotary: scip on _grblExecProgress=',self._grblExecProgress)
            return
        if self._mPosInited :
          self.gui.upd_rotary()
 





          
       


    def button_red_callback(self,pin,button): # right key
        print('button_red_callback  self._grblExecProgress=', self._grblExecProgress, self.grblParams['_state'])
        if self._grblExecProgress in ('do','doing','alarm','error') or self.grblParams['_state'] in ('alarm','error') :
          self.send2grblOne('cancel')
          self.send2grblOne('^')
          #machine.soft_reset()
          
        else:  
          if self.gui._ui_modes[self.gui._ui_mode] == 'confirm':
            self._ui_confirm='no'
            self.gui._ui_mode= self.gui._ui_mode_prev
          else:
            self.gui.nextUiMode(1) 
           
             

    def button_red_callback_long(self,pin,button):
        print('button_red_callback_long')
 
    def button_yellow_callback(self,pin,button):
        print('button_yellow_callback')
        if self.gui._ui_modes[self.gui._ui_mode] == 'confirm':
          self._ui_confirm='yes'
          self.gui._ui_mode= self.gui._ui_mode_prev
        else:
          self.gui.nextUiMode(-1) 


    def button_yellow_callback_long(self,pin ,button):
        print('button_yellow_callback_long')

