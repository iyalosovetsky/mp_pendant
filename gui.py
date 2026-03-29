import usocket as socket
import uselect as select
import sys

import time



from nanoguilib.writer import CWriter
from nanoguilib.meter import Meter
from nanoguilib.label import Label, ALIGN_LEFT, ALIGN_RIGHT, ALIGN_CENTER 
from nanoguilib.textbox import Textbox
from nanoguilib.colors import *

# Fonts
import nanoguilib.arial10 as arial10
import nanoguilib.courier20 as fixed
import nanoguilib.arial35 as arial35
import os
from nanoguilib.nanogui import refresh
from machine import  Pin
from button import Button
from ns2009 import Touch
from array import array
from template import Template



Y_POS_LABEL_PARAMS=280
PARAMS_IN_ROW=3
PARAMS_IN_COL=3

#VFD0_PURPLE = 0x00FFD2
#VFD0_GREEN = 0x30BF30
#VFD0_RED = 0xCF3030
#VFD0_BLUE = 0x4040CF
#VFD0_YELLOW = 0xFFFF00
#VFD0_YELLOW2 = 0xBFBF00
#VFD0_WHITE = 0xCFCFCF

# VFD_GRAY = 0x0016 #0x0019 0x001A 0x0006 0x0009
# VFD_PURPLE = 0x0017 #0x0007
# VFD_GREEN = 0x0011 #0x0001 0x0021
# VFD_RED = 0x0002
# VFD_LBLUE = 0x0008 #0x0018
# VFD_BLUE = 0x0004 #0x0014
# VFD_YELLOW = 0x0015 #0x0015 ssd.rgb(0xFF,0xff,0x00)
# VFD_YELLOW2 = VFD_YELLOW-12
# VFD_WHITE = 0xffff
# VFD_BLACK = 0x0000

# VFD_GRAY = GREY #0x0019 0x001A 0x0006 0x0009
# VFD_PURPLE = MAGENTA #0x0007
#VFD_GREEN = GREEN #0x0001 0x0021
#VFD_RED = RED
#VFD_LBLUE = CYAN #0x0018
#VFD_BLUE = BLUE #0x0014
#VFD_YELLOW = YELLOW #0x0015 ssd.rgb(0xFF,0xff,0x00)
#VFD_YELLOW2 = VFD_YELLOW
#VFD_WHITE = WHITE
#VFD_BLACK = BLACK






VFD_ARROW_X = RED
VFD_ARROW_Y = GREEN
VFD_ARROW_Z = BLUE
VFD_LABEL_X = WHITE
VFD_LABEL_Y = WHITE
VFD_LABEL_Z = WHITE
VFD_BG = BLACK

X_ARROW_COLOR = 'red'
Y_ARROW_COLOR = 'green'
Z_ARROW_COLOR = 'lblue'
ICON_COLOR = 'white'

DXYZ_STEPS=[0.05,0.1,1.,10.]
C_STEP_MAX = 100.0
C_STEP_MIN = 0.1

C_STEP_Z_MAX = 20.0
C_STEP_Z_MIN = 0.1

C_FEED_JOG_MAX = 5000.0
C_FEED_JOG_MIN = 20.0

C_FEED_RUN_MAX = 5000.0
C_FEED_RUN_MIN = 20.0



FEED_JOG_STEPS=[10.,100.,200.,500.,1000.]
FEED_RUN_STEPS=[10.,100.,200.,500.,1000.]


PENDANT_READ_INTERVAL =  300000000 # 0.3s in nanoseconds for pop cmd to grbl
GRBL_QUERY_INTERVAL_RUN = 500000000  # 0.5s in nanoseconds
MAX_BUTTON_BUFFER_SIZE=20

BLANK_SCREEN_MS = 3600_000  # 3660s -> 1 hour




DEBUG= False


# HTML сторінка з діалогом вибору файлу
html_page = """HTTP/1.1 200 OK
Content-Type: text/html

<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>MicroPython Upload</title></head>
<body>
    <h2>Завантаження файлу на пристрій</h2>
    <form action="/upload" method="post" enctype="multipart/form-data">
        <input type="file" name="file">
        <input type="submit" value="Завантажити">
    </form>
</body>
</html>
"""

class NeoLabelObj(object):
    def __init__(self, fgcolor:int , scale:float,x:int,y:int,text:str = '',label=None,fldLabel=None,
                 oneWidth:int=20, nlines:int=1, align = ALIGN_LEFT, bdcolor=None, invert=False, hidden = False,rotaryScale=1.0):
        self.x= x
        self.y= y
        self.text=  text
        self.scale= scale
        self.rotaryScale= rotaryScale
        self.fgcolor= fgcolor
        self.fgcolor_default= fgcolor
        self.bdcolor= bdcolor
        self.invert= invert
        self.nlines = nlines  
        self.label= label
        self.fldLabel = fldLabel
        self.height= self.label.height
        if fldLabel is None:
          self.width= self.label.width
        else:
          #self.width= self.label.width + self.fldLabel.width  
          self.width = max(self.label.width+  abs(self.label.col-self.fldLabel.col),self.label.width + self.fldLabel.width)
          #print("Width label: lw=",self.label.width ,'l.col=', self.label.col," Width field: fw=",self.fldLabel.width ,'f.col=', self.fldLabel.col,'self.width=',self.width)

          
          
        self.oneWidth= oneWidth
        self.charsl=5
        self.hidden = hidden
        self.align =  align
        self.chars = 5
        if self.width is not None and self.oneWidth is not None and self.oneWidth>0 and self.width>0 :
          # self.charsl=self.width//self.oneWidth + (1 if (self.width%self.oneWidth)>0 else 0)
          self.charsl=self.width//self.oneWidth 
          self.chars =self.charsl * self.nlines
        
        

def color2rgb(color:str):
    if color is not None and isinstance(color,str):
        if color.lower() == 'red':
          color = RED
        elif color.lower() == 'green':   
          color = GREEN
        elif color.lower() == 'blue':   
          color = BLUE
        elif color.lower() in ('lblue', 'lightblue','cyan'):   
          color = CYAN
        elif color.lower() == 'magenta':   
          color = MAGENTA      
        elif color.lower() == 'yellow':   
          color = YELLOW      
        elif color.lower() == 'white':   
          color = WHITE
        elif color.lower() in ('lred', 'lightred'):   
          color = LIGHTRED
        elif color.lower() in ('lgreen', 'lightgreen'):
          color = LIGHTGREEN  
        elif color.lower() in ('dgreen', 'darkgreen'):
          color = DARKGREEN
        elif color.lower() in ('dblue', 'darkblue'):
          color = DARKBLUE
        elif color.lower() in ('gray', 'grey'):
          color = GREY

        else:
           color = WHITE   
    return  color


class Gui(object ):

    _jog_arrow:str = ''
    _jog_value:float = 0.0
    _highlightedArea:str= 'x'
    _pressedX:int= None
    _pressedY:int= None
    _pressedOldX:int= None
    _pressedOldY:int= None
    rotaryObj=[{'obj':None ,'axe':'x','unit':1.0, 'value':0,'value_prev':0,'mpos':0,'nanosec':0, 'scale':1.0,'updated': False },
               {'obj':None ,'axe':'y','unit':1.0, 'value':0,'value_prev':0,'mpos':0,'nanosec':0, 'scale':1.0,'updated': False }]

    #_ui_modes=['main','drive','feedJog','feedRun','scaleXY','scaleZ','confirm'] #confirm must be last
    _ui_modes=['main','drive', 'template' ,'params','confirm'] #confirm must be last
    _ui_mode=0
    _ui_confirm='unkn'
    #_ui_mode_prev=0
    _ui_mode_prev=-1
    _dXY_jog:float = DXYZ_STEPS[2]
    _dZ_jog:float = DXYZ_STEPS[2]
    _dXY_run:float = DXYZ_STEPS[2]
    _dZ_run:float = DXYZ_STEPS[2]

    _feedrateJog:float =  FEED_JOG_STEPS[2]
    _feedrateRun:float =  FEED_JOG_STEPS[2]

    term_line_from:int = 1
    term_pos_from:int = 0    
    _editCmd:str = ''

    neo_refresh:bool = False

    pin_yellow=None
    button_yellow=None
    pin_red=None
    button_red=None
    ns=None

    grblButtonHist=[]
    buttonInCounter=0

    _blank=False
    _touched=time.ticks_ms()
    

    debug:bool = DEBUG
    enable_invert_on_select = True
    templ_files = []
    template = None
    labels = {}  # dictionary of configured messages_labels
    templ_labels = {}  # dictionary to store params of template macro
    _msg_conf = [   #name, mode_list,textline default, fgcolor, x, y, scale, width, nlines,align
            ('zeroX', ['main','drive'], 'X'                         , X_ARROW_COLOR   ,  142,  35,  3, 40    ,1, ALIGN_RIGHT), 
            ('zeroY', ['main','drive'], 'Y'                         , Y_ARROW_COLOR   ,  142, 115,  3, 40    ,1, ALIGN_RIGHT),
            ('zeroZ', ['main','drive'], 'Z'                         , Z_ARROW_COLOR   ,  142, 195,  3, 40    ,1, ALIGN_RIGHT),
            ('x', ['main','drive'], '{:6.2f}'.format(-230.1)         , X_ARROW_COLOR   ,  142+25+10,  35,  3, 126    ,1, ALIGN_RIGHT), 
            ('y', ['main','drive'], '{:6.2f}'.format(-230.1)         , Y_ARROW_COLOR   ,  142+25+10, 115,  3, 126    ,1, ALIGN_RIGHT),
            ('z', ['main','drive'], '{:6.2f}'.format(-230.1)         , Z_ARROW_COLOR   ,  142+25+10, 195,  3, 126    ,1, ALIGN_RIGHT),
            ('mx', ['main','drive'], '{:6.2f}'.format(0.0)       , X_ARROW_COLOR   ,  142+25+10+30,  35+40,  2, 126    ,1, ALIGN_RIGHT), 
            ('my', ['main','drive'], '{:6.2f}'.format(0.0)       , Y_ARROW_COLOR   ,  142+25+10+30, 115+40,  2, 126    ,1, ALIGN_RIGHT),
            ('mz', ['main','drive'], '{:6.2f}'.format(0.0)       ,Z_ARROW_COLOR    ,  142+25+10+30, 195+40,  2, 126    ,1, ALIGN_RIGHT),
            ('dXY', ['main','drive'], '{:4.0f}'.format(_dXY_jog  )        , Y_ARROW_COLOR   ,  142+10, (115-35)//2+35+10,  2, 60    ,1, ALIGN_RIGHT),
            ('dZ', ['main','drive'], '{:4.0f}'.format(_dZ_jog)          , Z_ARROW_COLOR   ,  142+10, 195+40 ,  2, 60    ,1, ALIGN_RIGHT),
            ('cmd', ['main','drive'], '#G29 some command grbl'      , 'white'         ,    0, 255,  2, 308    ,1, ALIGN_LEFT),  #14*22
            ('feed', ['main','drive'], '{:4.0f}'.format(_feedrateJog)    , 'white'   ,  0,  0,  2, 6*15-1,1, ALIGN_LEFT),
            ('state', ['main','drive'], 'Idle'    , 'white'         ,  6*14,  0,  2, 310-120,1, ALIGN_LEFT),
            ('mpg', ['main','drive'], 'noMPG G57'    , 'white'         ,  180,  0,  2, 310-120,1, ALIGN_RIGHT),
            ('term', ['template','params'], 'F1 - Help' , 'white'         ,             0,  40,  2, 140          ,10, ALIGN_LEFT),
            ('spindeOn', ['main','drive'], 'ON'           ,  'green'       ,   10, 370,  3, 60     ,1, ALIGN_LEFT),
            ('home', ['main','drive'], 'HOME'           ,  'yellow'        ,  110, 370,  3, 60     ,1, ALIGN_CENTER),
            ('spindeOff', ['main','drive'], 'OFF'           ,  'red'        ,  250, 370,  3, 60     ,1, ALIGN_RIGHT),
            ('info', [], 'info'                        , 'white'         ,    0, 280,  2, 318    ,4, ALIGN_LEFT),  #6*51
            ('<', [], '<<'           ,  'yellow'       ,   10, 405,  3, 60     ,1, ALIGN_LEFT),
            ('icon', [], '     main     ' , ICON_COLOR, 20+3*14,  410, 2, 250-20-3*14    ,1, ALIGN_CENTER),
            ('>', [], '>>'           ,  'lblue'        ,  270, 405,  3, 60     ,1, ALIGN_LEFT)

        ]
    help = [
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

    gridX0=5
    gridY0=50
    gridStep=20
    gridCount=7

    imageX0=150
    imageY0=50
    imageStep=20
    imageCount=7

    toolPoly=array('h', [6, 0,\
                        6, 2,\
                        3, 5,\
                        0, 2,\
                        0, 0\
                        ])             
    cncFieldXmax=700
    cncFieldYmax=700
    gridMax=(gridCount-1)*gridStep
    cncFieldKX=gridMax/cncFieldXmax
    cncFieldKY=gridMax/cncFieldYmax

    imageMax=(imageCount-1)*imageStep

    _xToolCnt=0
    _xToolPrev=None 
    _yToolPrev=None

    ip = None
    server = None
    poller = None




    def __init__(self, neo, grblParams,
                  grblParserObj,
                  templateDir='/templates',
                  debug:bool = DEBUG):
       
       self.neo=neo
       self.ns = Touch(isLandscape=False)
       self.ns.set_int_handler(self.touchscreen_press)
       self.grblParams=grblParams
       self.grblParserObj=grblParserObj
       self.templateDir = templateDir




       self.debug=debug
       self._touched=time.ticks_ms()
       self.neoInit()
       #self.hello()
       

    @property
    def state(self):
        return self.grblParams._state
    
    def refresh(self,clear=None):
       self.neo_refresh= False
       self.neoBlank(time.ticks_diff(time.ticks_ms(),self._touched)>BLANK_SCREEN_MS)
       refresh(self.neo,clear)

    def setYellowButton(self,pin:int):
       self.pin_yellow=Pin(pin, Pin.IN, Pin.PULL_UP)
       self.button_yellow=Button(pin=self.pin_yellow,callback=self.button_red_callback,callback_long=self.button_red_callback_long)

    def setRedButton(self,pin:int):
       self.pin_red=Pin(pin, Pin.IN, Pin.PULL_UP)
       self.button_red=Button(pin=self.pin_red,callback=self.button_yellow_callback,callback_long=self.button_yellow_callback_long)



    # --- 2. HTTP Server Setup ---
    def start_http(self,ip):
        # Bind to port 80 (HTTP)
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #self.http_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) 
        host = '0.0.0.0'
        port = 80
        self.server.bind((host, port))
        self.server.listen(5)
        self.server.setblocking(False) # Set to non-blocking mode
        # Реєстрація сокета для опитування на подію POLLIN (вхідні дані/підключення)

        self.poller = select.poll()
        self.poller.register(self.server, select.POLLIN)
        print(f"Listening on {host}:{port}")

        
    def save_clean_file(self, conn, filename= "uploaded2_file.py"):
      try:
          # 1. Читаємо перший шматок, щоб знайти межу (boundary) та кінець HTTP-заголовків
          data = conn.recv(1024)
          fn=None
          lfilename=filename
          # Шукаємо порожній рядок \r\n\r\n, який відділяє HTTP-заголовки від тіла
          header_end = data.find(b'\r\n\r\n')
          if header_end == -1: return None
          #print("Header received,  :", data[:header_end])
          for items in data[:header_end].split(b'\r\n'):
              if b'Content-Disposition:' in items:
                  #print("Content-Disposition found:", items)
                  for items in data[:header_end].split(b';'):
                      if b'filename=' in items:
                          filename2 = items.split(b'filename=')[1].strip().strip(b'"').decode().replace('"','').strip()
                          #print("Filename extracted:", filename2)
                          if  filename2.find('.py') >=0 :
                            lfilename = 't'+filename2[:filename2.find('.py')]+'.py' # add prefix and suffix to avoid executing uploaded file as template
                            break
                          else:
                             print( filename2, filename2.find('/')   , filename2.find('\\')  )
                  break
          else:
              print("filename2 not found in headers.")
          
          
          print("Filename to save :", self.templateDir + "/" + lfilename,filename)
          # Тіло запиту починається після \r\n\r\n
          body_start = data[header_end+4:]
          
          # Шукаємо межу multipart (вона після Content-Type заголовків файлу)
          file_start = body_start.find(b'\r\n\r\n')
          #if file_start == -1: return False
          if file_start == -1: 
             actual_data = body_start
          else:   
            # Реальний вміст файлу починається тут
            actual_data = body_start[file_start+4:]
          ii=0
          fn=self.templateDir + "/" + lfilename
          with open(fn, "wb") as f:
              f.write(actual_data)
              ii+=1
              # 2. Читаємо решту даних потоком
              while True:
                  ii+=1
                  chunk = conn.recv(1024)
                  if not chunk: break
                  
                  # Шукаємо фінальну межу (boundary)
                  # Спрощення: якщо знаходимо '--', це зазвичай кінець форми
                  boundary_pos = chunk.find(b'\r\n--')
                  if boundary_pos != -1:
                      f.write(chunk[:boundary_pos])
                      break
                  f.write(chunk)
          
          print("Файл очищено та збережено:", fn)
          return fn
      except Exception as e:
          if ii>0:
                print(f"Записано частково, байт: {ii*512} - ",fn, e)
                return fn
          else:
              print("Помилка парсингу:", e)
          return None
      





    def httpTask(self):
      if self.server is None:
        return

      events = self.poller.poll(100)
      
      for fd, ev in events:
          if ev & select.POLLIN:
              # Маємо нове підключення
            try:  
              conn, addr = self.server.accept()
              conn.setblocking(True) # Тимчасово блокуємо для стабільного читання заголовків
              print('Client connected from', addr)

              
              # Для завантаження файлів краще на мить перейти в блокуючий режим
              conn.settimeout(5.0) 
              request = conn.recv(1024).decode()
              
              print("Request received:", request)
              if "GET / " in request:
                    # Віддаємо головну сторінку з формою
                    conn.send(html_page)
                
              # --- 3. Process POST request ---
              elif "POST /upload" in request:
                  # Find body part (separated by \r\n\r\n)
                  fn=self.save_clean_file(conn)

                  if fn is not None:
                        conn.send("HTTP/1.1 200 OK\r\n\r\nFile Saved!"+fn)
                  else:
                        conn.send("HTTP/1.1 500 Error\r\n\r\nWrite Failed")                  
                  # if len(parts) > 1:
                      # body = parts[1]
                      # print("POST Data Received:", len(body), "bytes")
                      
                      # Example of acting on data: JSON parsing
                      # data = json.loads(body)
                      
                      # Send HTTP Response (OK)
                      # response = "HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n\r\n"
                      # response += '{"status": "success"}'
                      # conn.send(response)
                      # conn.send("HTTP/1.1 200 OK\r\n\r\nFile received (simulated)")

                  # else:
                      # conn.send("HTTP/1.1 400 Bad Request\r\n\r\n")
              else:
                  # Basic home page for GET request
                  conn.send("HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n")
                  conn.send("<h1>MicroPython POST Server</h1>")

              conn.close()
            except OSError as e:
                    conn.close()
                    print('Connection closed')
            except Exception as e:
              
              conn.close()
              print("інша помилка:", e)
        
        
        



    def button_red_callback(self,pin,button): # right key
      if self._ui_modes[self._ui_mode] == 'confirm': # for approve confirm dialog
        self.procButtons([0,1,1, self._highlightedArea ])
      else:
        self.pushButtons(btnN=1,state=1)
             

    def button_red_callback_long(self,pin,button):
        self.pushButtons(btnN=1,state=2)
        
 
    def button_yellow_callback(self,pin,button):
      if self._ui_modes[self._ui_mode] == 'confirm': # for approve confirm dialog
        self.procButtons([0,0,1, self._highlightedArea ])
      else:
        self.pushButtons(btnN=0,state=1)


    def button_yellow_callback_long(self,pin ,button):
        self.pushButtons(btnN=0,state=2)



    def initTemplate(self):
      self.template=Template(template_name=self.templ_files[self._current_template_idx])
      if self.template is not None and self.template.app is not None :  
          
          ii=0
          cmds=self.template.app.getGcode()
          if isinstance(cmds,str):
            print('button_yellow_callback: template mode, string mode template=',cmds)
            cmds=cmds.splitlines()
          else:
            print('button_yellow_callback: template mode, list mode  template=',cmds)





          for cmd in cmds:
              #self.grblParserObj.send2grbl(cmd) todo unmark after develop
              ii+=1
              #if ii==1:
              #   print('point11',cmd) 
          print('len 2send',len(self.grblParserObj.grblCmd2send),ii,self.template.params)  
          self.neoDisplayTemplate(template_name =self.template.template_name)


    def procButtons(self,buttonEvent):
          if buttonEvent[1]==0: #yellow
            if buttonEvent[2]==2: #long
              print('button_yellow_callback_long')
              if self.grblParserObj._grblExecProgress in ('do','doing','alarm','error'):
                  print ('button_yellow_callback_long: skip on _grblExecProgress=',self.grblParserObj._grblExecProgress)
                  return 1       
              if self._ui_modes[self._ui_mode] in ( 'main'):
                if self.rotaryObj[0]['axe'] in ('x','y','z'):
                  self.grblParserObj.send2grblOne('zero'+self.rotaryObj[0]['axe'].upper())
                  return 0
            elif buttonEvent[2]==1: #normal
              if self._ui_modes[self._ui_mode]=='params' and len(buttonEvent)>=5 and buttonEvent[3] is not None and buttonEvent[4] is not None:
                  #print('point203: todo put params to grbl',l_buttonEvent)
                  cmd=buttonEvent[3][buttonEvent[3].find('.')+1:]+'='+buttonEvent[4][:buttonEvent[4].find('.')+4]
                  self.grblParserObj.send2grbl(cmd)
                  self.grblParserObj.queryParams()               
              elif self._ui_modes[self._ui_mode] == 'confirm':
                self._ui_confirm='yes'
                self._ui_mode= self._ui_mode_prev if self._ui_mode_prev>=0 else 0
                #print('button_yellow_callback222: confirm mode, self._ui_confirm_prev=',self._ui_modes[self._ui_mode])
                
                if buttonEvent[3] in ('zeroX','zeroY','zeroZ') and len(buttonEvent)>=4 and buttonEvent[3] is not None:
                  self.grblParserObj.send2grblOne(buttonEvent[3])
                  #self.nextUiMode(to_mode=self._ui_mode_prev, refresh=True)
                  self.leave2PrevAfterConfirm(self._ui_mode_prev)
                elif buttonEvent[3] in ('spindeOn','spindeOff', 'home') and len(buttonEvent)>=4 and buttonEvent[3] is not None:
                  self.grblParserObj.send2grblOne(buttonEvent[3])
                  self.leave2PrevAfterConfirm(self._ui_mode_prev)
                elif self._ui_modes[self._ui_mode]=='template' and self.template is not None:
                  self.template.updateParams()
                  cmds=self.template.app.getGcode()
                  if isinstance(cmds,str):
                        #print('button_yellow_callback222: template mode, string mode template=',cmds)
                        cmds=cmds.splitlines()
                  else:
                        print('button_yellow_callback2222: template mode, list mode  template=',cmds)
                  #newParams=self.template.params
                  #print('button_yellow_callback2222: newParams=',newParams) 
                  ii=0
                  self._ui_mode=1 #drive mode after confirm template
                  #self.nextUiMode(to_mode=1, refresh=True)
                  self.leave2PrevAfterConfirm(to_mode=1)

                  for cmd in cmds:
                          self.grblParserObj.send2grbl(cmd) #todo unmark after develop
                          ii+=1
                          if ii==1:
                            print('point11',cmd) 
                  print('len 2send2222',len(self.grblParserObj.grblCmd2send),ii,self.template.params)
                  
                      



              else:
                if self._ui_modes[self._ui_mode] == 'drive' \
                  and (self.grblParams._dX2go!=0 or self.grblParams._dY2go!=0 or self.grblParams._dZ2go!=0):
                  cmd='G91 G1'
                  if self.grblParams._dX2go!=0:
                    cmd+=' X{0:.3f}'.format(self.grblParams._dX2go)
                  if self.grblParams._dY2go!=0:
                    cmd+=' Y{0:.3f}'.format(self.grblParams._dY2go)
                  if self.grblParams._dZ2go!=0:
                    cmd+=' Z{0:.3f}'.format(self.grblParams._dZ2go)
                  if self._feedrateRun>0:
                    cmd+=' F{0:.0f}'.format(self._feedrateRun)
                  else:
                    cmd+=' F{0:.0f}'.format(50)  
                  
                  self.grblParserObj.mpgCommandShow(cmd)
                  self.grblParams._dX2go=0.00
                  self.grblParams._dY2go=0.00
                  self.grblParams._dZ2go=0.00
                elif self._ui_modes[self._ui_mode] == 'template':
                  print('button_yellow_callback: template mode, ',self._current_template_idx)
                  if self._current_template_idx is not None and self._current_template_idx>=0 and self._current_template_idx<len(self.templ_files):
                      self.initTemplate()




                else:  
                    #self.nextUiMode(-1) 
                    print('button_yellow_callback no switch mode')






          elif buttonEvent[1]==1: #red
            if buttonEvent[2]==2: #long
              print('button_red_callback_long')
              return 0
            elif buttonEvent[2]==1: #normal
              print('button_red_callback  self.grblParserObj._grblExecProgress=', self.grblParserObj._grblExecProgress, self.grblParams._state)
              if self.grblParserObj._grblExecProgress in ('do','doing','alarm','error') or self.grblParams._state in ('alarm','error') :
                self.grblParserObj.send2grblOne('cancel')
                self.grblParserObj.send2grblOne('^')
                #machine.soft_reset()
                return 0
              else:  
                if self._ui_modes[self._ui_mode] == 'confirm':
                  self._ui_confirm='no'
                  #self.nextUiMode(to_mode=self._ui_mode_prev, refresh=True)
                  self.leave2PrevAfterConfirm(self._ui_mode_prev)
                else:
                  #self.nextUiMode(1)                
                  print('button_red_callback no switch mode')

                return 0  
          return 0  


    def pushButtons(self,btnN,state):
       self._touched=time.ticks_ms()
       self.neoBlank(False)
       while len(self.grblButtonHist)>MAX_BUTTON_BUFFER_SIZE:
          self.grblButtonHist.pop(0)
       #print('point200:',self._highlightedArea,btnN,state)   
       if self._current_template_idx>=0 and self._highlightedArea.startswith('$$') :
          #print('point201: axe, param [idx] ',self._highlightedArea,self.rotaryObj[0]['axe'],self.grblParserObj._cnc_params[self._current_template_idx])
          ff=self.grblParserObj._cnc_params[self._current_template_idx]
          #print('point202: ff ',ff)
          self.grblButtonHist.append([self.buttonInCounter,btnN,state, '$$.' + ff[0],ff[1]] )            
       else:   
          self.grblButtonHist.append([self.buttonInCounter,btnN,state, self._highlightedArea ] )            

    def neoBlank(self, blank = True):
       if self._blank!=blank or self.neo._blank!=blank:
        self._blank=blank
        self.neo._blank=self._blank
        if not self._blank:
           self.neo_refresh= True
        #print("neoBlank:",self._blank)

    def toolMapX(self,x):
       if x is None:
          return None
       pos=x*self.cncFieldKX
       if pos>self.gridMax :
          return self.gridX0+self.gridMax
       elif pos<=0:
          return self.gridX0
       else:
          return self.gridX0+int(pos)

    def toolMapY(self,y):
       if y is None:
          return None
       pos= self.gridMax-y*self.cncFieldKX
       if pos>self.gridMax :
          return self.gridY0+self.gridMax
       elif pos<=0:
          return self.gridY0
       else:
          return self.gridY0+int(pos)


    def neoGrid(self):
        #self.neoLabel(text='',id='term',hidden=True)
        self.neo.fill_rect(self.gridX0,self.gridY0,self.gridMax,self.gridMax,BLACK)
        for ii in range(self.gridCount):
          self.neo.hline(self.gridX0,self.gridY0+ii*self.gridStep,self.gridMax,GREY)
          self.neo.vline(self.gridX0+ii*self.gridStep,self.gridY0,self.gridMax,GREY) 
        self._xToolPrev=None 
        self._yToolPrev=None

    def neoTemplateImage(self):
        #self.neoLabel(text='',id='term',hidden=True)
        self.neo.fill_rect(self.imageX0,self.imageY0,self.imageMax,self.imageMax,BLACK)
        for ii in range(self.imageCount):
          self.neo.hline(self.imageX0,self.imageY0+ii*self.imageStep,self.imageMax,GREY)
          self.neo.vline(self.imageX0+ii*self.imageStep,self.imageY0,self.imageMax,GREY)
        if self.template is not None and self.template.app is not None:  
          try:
             img=self.template.app.getIcon()
             if img is not None:
                # print('neoTemplateImage: got template image, size=',len(img),img[:10])
                #[{'name': 'quadrant', 'height': 10.0, 'fill': True, 'color': 'red', 'shape': 'rect', 'width': 10.0}]
                #[{'name': 'circle', 'height': 5.0, 'fill': True, 'color': 'blue', 'shape': 'ellipse', 'width': 5.0}]
                max_dim=0
                for item in img:
                    w=item.get('width',1.0)
                    h=item.get('height',1.0)
                    if w>max_dim:
                        max_dim=w
                    if h>max_dim:
                        max_dim=h
                # print('neoTemplateImage: max_dim=',max_dim,' imageMax=',self.imageMax)        
                K= self.imageMax*0.8/max_dim if max_dim>0 else 0.8 
                # print('neoTemplateImage: scale K=',K)
                origin_color=WHITE  
                for item in img:
                    color=color2rgb(item.get('color','white'))
                    shape=item.get('shape','rect')
                    fill=item.get('fill',False)
                    w=int(item.get('width',0.)*K)
                    h=int(item.get('height',0.)*K)
                    x=int(self.imageX0+5+int(item.get('x',0.)*K))
                    y=int(self.imageY0+5+int(item.get('y',0.)*K))
                    if shape=='rect':
                        # print('neoTemplateImage: point2 rect ',x,y,w,h,color,fill) 
                        self.neo.fill_rect(x,y,w,h,color) if fill else self.neo.rect(x,y,w,h,color)
                        if color==WHITE:
                          origin_color=GREEN
                    elif shape=='ellipse':
                        # print('neoTemplateImage: point3 ellipse ',x,y,w,h,color,fill) 
                        self.neo.fill_ellipse(x,y,w//2,h//2,color) if fill else self.neo.ellipse(x,y,w//2,h//2,color)
                        if color==WHITE:
                          origin_color=GREEN
                    elif shape=='origin':
                        # print('neoTemplateImage: point3 ellipse ',x,y,w,h,color,fill) 
                        self.neo.fill_ellipse(x,y,3,3,origin_color) 



          except Exception as e:             print('Error displaying template image:', e)
           


    def neoTool(self,X,Y):
      if X is None or Y is None :
          return
      gridNowX=self.toolMapX(X)
      gridNowY=self.toolMapY(Y)
      if gridNowX is None or gridNowY is None:
          return
      
      gridPrevX=self.toolMapX(self._xToolPrev)
      gridPrevY=self.toolMapY(self._yToolPrev)
      if  self._xToolPrev is not None and self._yToolPrev is not None and gridPrevX==gridNowX and gridPrevY==gridNowY:
         return
      
      self._xToolCnt+=1  
      if self._xToolPrev is not None and self._yToolPrev is not None:
         tool=(gridPrevX-3,gridPrevY-6)
         self.neo.poly(tool[0],tool[1], self.toolPoly, BLACK,True )
         if self._xToolCnt%10==0:
            self.neoGrid()
      else: 
         self.neoGrid()  
      tool=(gridNowX-3,gridNowY-6)
      self.neo.poly(tool[0],tool[1], self.toolPoly, YELLOW,True )
      self._xToolPrev=X
      self._yToolPrev=Y
      
       
      



    def neoInit(self):
       #self.labels=self.neoDrawAreas(self._msg_conf)
       self.neoHighLight(id=self._highlightedArea, labels=self.labels)
       
       self.neo_refresh= True
       self.templ_labels = {}  # dictionary of configured messages_labels
       self.show_MPG()
       self.neoGrid()
       self.refreshUiMode()
                 
    # initialize neo display labels
    def neoDrawAreas(self, config_array=[]):
        labels = {}  # dictionary of configured messages_labels
        for c1 in config_array:
            
            (name, mode_list, textline, fgcolor, x, y, scale, width, nlines,align ) = c1  # unpack tuple into five var names
            if len(mode_list)>0 and self._ui_modes[self._ui_mode] not in mode_list: continue
            fgcolor = color2rgb(fgcolor)
            p=name.find('.')

            fnt=arial35 if scale==3 else (arial10 if scale==1 else fixed)
            writer = CWriter(self.neo, fnt, verbose=self.debug)
            writer.set_clip(False, False, False) #row_clip=None, col_clip=None, wrap=None

            rotaryScale=1.0
            

            if p>=0:
              name2=name[p+1:]
              if name2 =='OK':
                ll=Label(writer, y, x, textline, fgcolor=fgcolor, bdcolor=False, align=ALIGN_CENTER)
                labels[name] = NeoLabelObj(text  = textline, fgcolor=fgcolor, bdcolor=False , align=align, scale=scale,x=x,y=y,label=ll, oneWidth=writer.stringlen('0'))
              else:    
                flw=writer.stringlen('quadrant ')+2
                fl=Label(writer, y, x, (name2[:8]).upper()+' ',fgcolor=GREEN)
                #print('neoDrawAreas:', name,name2, textline, x+flw, y)
                if name.startswith('$$'):
                   val=float(textline)
                else:    
                  val=self.template.params.get(name2,00.01)
                ll=Label(writer, y, x+flw, '{:6.2f}'.format(val), bdcolor=False, fgcolor=fgcolor, align=align)
                rotaryScale= 0.01 if val<=1.0 else (0.1 if val<=10.0 else (1.0 if val<=100.0 else 10.0))
                labels[name] = NeoLabelObj(text  = textline, fgcolor=fgcolor, bdcolor=False , align=align, scale=scale,x=x,y=y,label=ll,fldLabel=fl, oneWidth=writer.stringlen('0'),rotaryScale=rotaryScale)
            else: #name in ('xyz','zeroX','zeroY','zeroZ','spindeOn','spindeOff','home','state','cmd','icon','mx','my','mz','dXY','dZ'):
              if name in ('mx','my','mz','dXY','dZ'):
                rotaryScale=0.1
              elif name in ('feed'):
                rotaryScale=10.0
              else:                
                rotaryScale=1.0  
              if name in ('info','term'):
                ll=Textbox(writer, clip=False, row=y, col=x, width=width, nlines=nlines, bdcolor=False, fgcolor=fgcolor,bgcolor=VFD_BG)
              else:
                ll=Label(writer, y, x,textline, fgcolor=fgcolor, bdcolor=False, align=align)

              labels[name] = NeoLabelObj(text  = textline, fgcolor=fgcolor , bdcolor=False, align=align, scale=scale,x=x,y=y,label=ll, oneWidth=writer.stringlen('0'),rotaryScale=rotaryScale)


        return labels


    # ui label`s updater
    #def neoLabel(self,text,id='info',color=None,currentLine=None, hidden=None, force=False):
    def neoLabel(self,text,id,color=None,currentLine=None, hidden=None, force=False):
        if not id in self.labels:
            return
        if hidden is not None :
          if hidden and self.labels[id].hidden and not force:
              return
          self.labels[id].hidden = hidden        
        if self._blank:
           return
        self.labels[id].text = text
        #if id=='state':
        #  self.labels[id].text += (' MPG' if self.grblParams._mpg else '   ')+(' '+self.grblParams._wcs if self.grblParams._wcs is not None else  '    ')
        


 

       

        if self.labels[id].hidden  :
          self.neoDraw(id, labels=self.labels, currentLine=currentLine)
          return  
        
            
        if id=='state' and text.lower().startswith('alarm'):
             self.labels[id].fgcolor=RED
        elif id=='state' and  (text.lower().startswith('run') or text.lower().startswith('jog')):
             self.labels[id].fgcolor=GREEN
        elif id=='feed' and text.lower().startswith('alarm'):
             self.labels[id].fgcolor=RED
        elif id=='feed' and (text.lower().startswith('run') or text.lower().startswith('jog')):
             self.labels[id].fgcolor=GREEN
        elif id=='info' and  text.find('Alarm')>=0:
             self.labels[id].fgcolor=RED
        elif id=='info' and  text.find('Jog')>=0:
             self.labels[id].fgcolor=GREEN
        elif id=='info' and  text.find('Run')>=0:
             self.labels[id].fgcolor=YELLOW
        elif id=='info' and  text.find('Hold')>=0:
             self.labels[id].fgcolor=GREY
        elif id=='info' and self.grblParams._mpg=='1':
             self.labels[id].fgcolor=CYAN
        elif id=='info' and self.grblParams._mpg!='1':
             self.labels[id].fgcolor=WHITE
        elif id=='mpg' and  self.grblParams._mpg=='1':
             self.labels[id].fgcolor=GREEN
        elif color is not None:
             self.labels[id].fgcolor=color2rgb(color)
        else:   
             self.labels[id].fgcolor= self.labels[id].fgcolor_default      

        self.neoDraw(id, labels=self.labels, currentLine=currentLine)     

    # ui terminal line position decrease
    def decTermLinePos(self):
       if len(self.grblParams._grbl_info)>0 and self.term_line_from>3:
          self.term_line_from -= 3

    # ui terminal position decrease
    def decTermPos(self):
       if len(self.grblParams._grbl_info)>0 and self.term_pos_from>4:
          self.term_pos_from -= 5


    # ui terminal line position increase
    def incTermLinePos(self):
        if len(self.grblParams._grbl_info)>0:
          lines = self.grblParams._grbl_info.count('\n')  
          lines += 1
          if self.term_line_from<lines:
             self.term_line_from += 3

    # ui terminal position increase
    def incTermPos(self):
        if len(self.grblParams._grbl_info)>0:
          if self.term_pos_from<50:
             self.term_pos_from += 5

    # ui terminal position home
    def homeTermPos(self):
        if len(self.grblParams._grbl_info)>0:
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
        #if cc.startswith('WCO:0.000,0.000,0.000'):
        #    continue
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
                       ''+(' {0:.1f}'.format(self._jog_value))
                       #+'f={0:.0f}'.format(self._feedrate)
                       ,color=color)


    def neoDisplayTemplate(self, template_name):
      self.neoLabel('','info',hidden=True, force=True)
      templ_config=[]
      xx=0
      yy=0
      ii=0
      xw=100
      yw=30
      rows=-1
         
      if template_name =='$$' :
        if len(self.grblParserObj._cnc_params)>0 and self._current_template_idx<len(self.grblParserObj._cnc_params) :
          #print('point2 ',self._current_template_idx,self.grblParserObj._cnc_params)
          ff=self.grblParserObj._cnc_params[self._current_template_idx] 
          xx=60
          yy=Y_POS_LABEL_PARAMS+30
          templ_config.append((template_name+'.'+ff[0],['params'], ff[1] , 'yellow'   ,  xx,  yy,  2, xw-10,1, ALIGN_RIGHT))
          rows=1
          #ii+=1
          #yy=int(yw*1.5)+Y_POS_LABEL_PARAMS    
          #xx=100
          #templ_config.append((template_name+'.OK', '   OK  ', 'yellow'   ,  xx,  yy,  2, xw-10,1, ALIGN_RIGHT))
      else:    
        rows=(len(self.template.params)+1+PARAMS_IN_ROW-1)//PARAMS_IN_ROW
        for param,val in self.template.params.items():
            xx=(ii%PARAMS_IN_ROW)*xw+10
            yy=(ii//PARAMS_IN_ROW)*yw+Y_POS_LABEL_PARAMS
            templ_config.append((template_name+'.'+param,['template'], '{0:.1f}'.format(val) , 'yellow'   ,  xx,  yy,  1, xw-10,1, ALIGN_RIGHT))
            ii+=1
        
        
        xx=int((ii%PARAMS_IN_ROW)*(xw+0.4))
        yy=(ii//PARAMS_IN_ROW)*yw+Y_POS_LABEL_PARAMS    
        templ_config.append((template_name+'.OK',['template'], '   OK  ', 'yellow'   ,  xx,  yy,  2, xw-10,1, ALIGN_RIGHT))

      

      if rows>=0:
        if template_name !='$$':
          for ii in range(rows+1) :
            self.neo.line(10,Y_POS_LABEL_PARAMS+ii*yw-10,310,Y_POS_LABEL_PARAMS+ii*yw-10,GREY)
          for ii in range(PARAMS_IN_ROW-1) :
            self.neo.line((ii+1)*xw+5,Y_POS_LABEL_PARAMS-15,(ii+1)*xw+5,Y_POS_LABEL_PARAMS+rows*yw-5,GREY)
      self.templ_labels=self.neoDrawAreas(templ_config)
      for ll in self.templ_labels:
          self.neoDraw(ll, labels=self.templ_labels)
      self.neo_refresh= True 

              

    def grblJog(self, x:float=0.0, y: float=0.0, z:float=0.0, feedrate:float=None):
      if feedrate is None:
         f=self.feedrate
      else:
         f=feedrate   
      cmd=''
      if x is not None and x!=0.0:
        self.set_jog_arrow(('+' if x>0 else '-')+'x',x)
        cmd=f'$J=G91 G21 X{x} F{f}'
        #MPG -> <Idle|MPos:30.000,0.000,0.000|Bf:35,1023|FS:0,0,0|Pn:HS|WCO:0.000,0.000,0.000|WCS:G54|A:|Sc:|MPG:1|H:0|T:0|TLR:0|Sl:0.0|FW:grblHAL>
      elif y is not None and y!=0.0:
        self.set_jog_arrow(('+' if y>0 else '-')+'y',y)
        cmd=f'$J=G91 G21 Y{y} F{f}'
      elif z is not None and z!=0.0:
        self.set_jog_arrow(('+' if z>0 else '-')+'z',z)
        cmd=f'$J=G91 G21 Z{z} F{f}'
      if cmd !='':
          self.neoLabel(cmd,id='cmd')  
          self.grblParserObj.mpgCommand(cmd+'\r\n')
          # self.query_now('grblJog') that is not needed, jog command returns status itself
          self.grblParserObj.p_RTSetNewInterval('autoQuery2grbl',GRBL_QUERY_INTERVAL_RUN)
          # if self.timeDelta2query != GRBL_QUERY_INTERVAL_RUN:
          #     self.timeDelta2query = GRBL_QUERY_INTERVAL_RUN
          # if self.time2query > time.time_ns()+self.timeDelta2query:
          #     self.time2query = time.time_ns()+self.timeDelta2query
          
          self.neoDisplayJog()               

    def neoPressedDrawPoint(self):
        if self._pressedX is not None and self._pressedY is not None:
            if self._pressedOldX is not None and self._pressedOldY is not None:
                self.neo.rect(self._pressedOldX-5,self._pressedOldY-5,10,10,VFD_BG,True)
            self.neo.rect(self._pressedX-5,self._pressedY-5,10,10,WHITE,True)
            self.neo_refresh= True

    # draw/update neo display label    
    def neoDraw(self,id, labels=None,currentLine=None):
        if id is not None:
            if labels is None:
                labels = self.labels

            if DEBUG:
                print('neoDraw['+id+']',labels[id].x,labels[id].y,labels[id].fgcolor,labels[id].text,labels[id].hidden)
                
            if labels[id].hidden:
                 if isinstance(labels[id].label,Textbox )  :
                    labels[id].label.clear()
                 else:
                    labels[id].label.value('')
                 return    

            if isinstance(labels[id].label,Textbox )  :
              if labels[id].invert:
                labels[id].label.bdcolor=CYAN
              else:
                labels[id].label.bdcolor=False  
              labels[id].label.clear()
              labels[id].label.fgcolor=labels[id].fgcolor
              #labels[id].label.append(labels[id].text[ : labels[id].chars])
              pos=0
              if currentLine is not None and currentLine>=labels[id].label.nlines and len(labels[id].text.splitlines())>labels[id].label.nlines:
                 pos=currentLine+1-labels[id].label.nlines
              labels[id].label.append(labels[id].text,ntrim=100,line=pos)
              labels[id].label.invertNLine=currentLine
              labels[id].label.show()

                 



            else:
              if id.find('.')>=0 :
                if labels[id].charsl-len(labels[id].text)>0  and (labels[id].align is None or labels[id].align==ALIGN_LEFT) :
                  labels[id].label.value( labels[id].text + ( " " * (labels[id].charsl + (1 if id not in('xyz') else 0)  - len(labels[id].text) ))   ,fgcolor=labels[id].fgcolor, align=labels[id].align, invert=False,bdcolor=(CYAN if labels[id].invert else False))
                else:    
                  labels[id].label.value(labels[id].text[:labels[id].charsl],fgcolor=labels[id].fgcolor, align=labels[id].align, invert=False,bdcolor=(CYAN if labels[id].invert else False))
              else:      
                if labels[id].charsl-len(labels[id].text)>0  and (labels[id].align is None or labels[id].align==ALIGN_LEFT) :
                  labels[id].label.value( labels[id].text + ( " " * (labels[id].charsl + (1 if id not in('xyz') else 0)  - len(labels[id].text) ))   ,fgcolor=labels[id].fgcolor, align=labels[id].align, invert=labels[id].invert,bdcolor=labels[id].bdcolor)
                else:    
                  labels[id].label.value(labels[id].text[:labels[id].charsl],fgcolor=labels[id].fgcolor, align=labels[id].align, invert=labels[id].invert,bdcolor=labels[id].bdcolor)
            
            self.neo_refresh= True





    def getHelp(self):
       self.helpIdx+=1
       self.helpIdx=self.helpIdx%len(self.help)
       return self.help[self.helpIdx]
       

    def neoIcon(self,text,color=None) :     
        self.neoLabel(text,id='icon',color=color2rgb(ICON_COLOR) if color is None else  color)            



    @property
    def step(self):
        return self._dXY_jog          

    @property
    def stepdZ(self):
        return self._dZ_jog          

    @property
    def mpg(self):
        return self.grblParams._mpg
    
    @property
    def mpg_prev(self):
        return self.grblParams._mpg_prev
    
    @property
    def state(self):
        return self.grblParams._state
    
    @property
    def state_prev(self):
        return self.grblParams._state_prev
    
    

    def neoWorkCoordinate(self, id:str):
      self.neoLabel('{0:.2f}'.format(getattr(self.grblParams, '_m' + id.upper()) - getattr(self.grblParams, '_w' + id.upper())), id=id)
      self.need_refresh = True
        

    def neoMachineCoordinate(self, id:str):
        if self._ui_modes[self._ui_mode] in ('main'):
          self.neoLabel('{0:.2f}'.format(getattr(self.grblParams, '_m' + id.upper())), id='m' + id)
        elif self._ui_modes[self._ui_mode] in ('drive'):  
          self.neoLabel('{0:.2f}'.format(getattr(self.grblParams, '_d' + id.upper()+'2go')), id='m' + id)

    def show_coordinates(self, id:str=None):
        if id is None:
            self.neoWorkCoordinate(id='x')
            self.neoWorkCoordinate(id='y')
            self.neoWorkCoordinate(id='z')
            self.neoMachineCoordinate(id='x')
            self.neoMachineCoordinate(id='y')
            self.neoMachineCoordinate(id='z')      
        else:
            self.neoWorkCoordinate(id=id)
            self.neoMachineCoordinate(id=id)    
        if self._ui_modes[self._ui_mode] in ('main'):
          self.neoTool(X=self.grblParams._mX,Y=self.grblParams._mY)  
        elif self._ui_modes[self._ui_mode] in ('drive'):  
          self.neoTool(X=self.grblParams._mX - self.grblParams._wX,Y=self.grblParams._mY - self.grblParams._wY)




    def show_params(self,pos=None)  :
      textline=''
      self.initRotaryStart()
      if self._ui_modes[self._ui_mode] in ('template'):
         textline='\n'.join([ff.replace('.py','') for ff in self.templ_files])
      elif self._ui_modes[self._ui_mode] in ('params'):
         self.grblParserObj._cnc_params_need_show = False
         textline='\n'.join([(ff[0][1:]+':'+ff[1])[:10] for ff in self.grblParserObj._cnc_params])
         self.neoDisplayTemplate(template_name ='$$')

                 

      else:
         return   
      
      if self.rotaryObj[0]['axe']!='icon' :
          self.rotaryObj[0]['axe']='term'
          self.neoHighLight(id='term',labels=self.labels)   


      if textline!='':
        if pos is not None:
            self._current_template_idx = pos
        self.neoTerm(textline,currentLine=self._current_template_idx,hidden=False)     



    def show_MPG(self): 
       self.grblParserObj._wcs_changed=False
       self.grblParserObj._mpg_changed=False
       self.neoLabel( ('MPG' if self.grblParams._mpg=='1' else 'noMPG') + \
                     (' '+self.grblParams._wcs if self.grblParams._wcs is not None else  '    ') + \
                     (' '+self.grblParams._pn if self.grblParams._pn is not None else  '    ')
                       ,id='mpg')

    def displayState(self,DisplayInfoLen=0):     
      if  self._ui_modes[self._ui_mode] in ('template','params'):
         return 
      if DisplayInfoLen>6 and self._ui_modes[self._ui_mode] in ('main','drive'):
         return 
      if 'info' in self.labels and not self.labels['info'].hidden and  DisplayInfoLen<3:
        self.neoLabel(self.grblParams._grbl_display_state,id='info')
      
      if self._ui_modes[self._ui_mode] in ('params') and self.grblParserObj._cnc_params_need_show:
         self.show_params(pos=0)
         

      self.show_coordinates()
      
      
      
      #if self.grblParserObj.state_is_changed() or self.grblParserObj._wcs_changed or self.grblParserObj._mpg_changed:
      if self.grblParserObj._wcs_changed or self.grblParserObj._mpg_changed:
         self.show_MPG()

      if self.grblParserObj.state_is_changed() or self.state == 'idle' or self.state.startswith('hold') :  
              if self.state.startswith('alarm'):
                  self._jog_arrow = ''
                  self.neoDisplayJog()
                  self.neoIcon('Alarm')
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


    def neoHighLight(self,id,labels=None):
        if labels is None:
            labels = self.labels  
        if id in labels:
              if not labels[id].invert:
                  labels[id].invert = True

                  if  (id in ('x','y','z','dXY','dZ','feed','mpg','icon','term') or id.find('.')>=0) and self.rotaryObj[0]['axe']!=id:
                    self.rotaryObj[0]['axe'] = id
                    if id in ('x','y','z'):
                      self.neoWorkCoordinate(id=id)
                    self.initRotaryStart()
                  elif id in ('zeroX','zeroY','zeroY') and self._ui_modes[self._ui_mode] in ('main','drive') and \
                        self.rotaryObj[0]['axe']!=id[4].lower():
                     self.rotaryObj[0]['axe'] = id[4].lower()
                     self.neoWorkCoordinate(id=id[4].lower())
                     self.initRotaryStart() 


                  self.neoDraw(id,labels=labels)
              for lIdx in labels:
                  if lIdx!=id:
                    if  labels[lIdx].invert and not labels[lIdx].hidden:
                        labels[lIdx].invert = False
                        if id in ('x','y','z'):
                            self.neoWorkCoordinate(id=id)
                        self.neoDraw(lIdx,labels=labels)
              self.neo_refresh =True          

    def touchscreen_press(self,x, y):
        # print('touchscreen_press:',x,y) 
        self._touched=time.ticks_ms() # lastotuched
        self.neoBlank(False)
        self._highlightedArea=''
        self._pressedOldX = self._pressedX
        self._pressedOldY = self._pressedY  
        self._pressedX = x
        self._pressedY = y
        

        for label in self.labels:
            if ((self._ui_modes[self._ui_mode] in ('template','params') and  label in ('<','>','term')) \
                
              or (self._ui_modes[self._ui_mode] in ('main','drive') and  label in ('x','y','z','<','>','dXY','dZ','feed','mpg','zeroX','zeroY','zeroZ','spindeOn','spindeOff','home')) ) \
              or  label in ('icon','term') \
                and not self.labels[label].hidden:
                if x>=self.labels[label].x-2 and x<=self.labels[label].x+self.labels[label].width+2 \
                  and y>=self.labels[label].y-2 and y<=self.labels[label].y+self.labels[label].height+2:
                    self._highlightedArea=label
                    
                    self.neoPressedDrawPoint()    
                    break
        if self._highlightedArea!='':
          print('  pressed ',self._highlightedArea)
          self.neoHighLight(id=self._highlightedArea,labels=self.labels)
          if self._highlightedArea in ('zeroX','zeroY','zeroZ','spindeOn','spindeOff','home') and self._ui_modes[self._ui_mode] in ('main','drive'):
            self._ui_confirm='OK'
            self.enterConfirmMode()
            self.neoIcon(text=self._ui_modes[self._ui_mode])
          elif self._highlightedArea in ('<','>'):
             self.nextUiMode(-1 if self._highlightedArea in ('<') else 1)
          # elif self._highlightedArea in ('term') and self._ui_modes[self._ui_mode] in ('template','params') and self._highlightedArea!=self.rotaryObj[0]['axe']!='term':   
          #    self.neoHighLight(id='term',labels=self.labels)
          #    self.neoTerm('\n'.join([ff.replace('.py','') for ff in self.templ_files]),currentLine=self._current_template_idx,hidden=False  )  
          elif self._highlightedArea in ('term') and self._ui_modes[self._ui_mode] in ('params') :   
             self.neoHighLight(id='term',labels=self.labels)
             self.grblParserObj.queryParams()
             
        elif self._ui_modes[self._ui_mode] in ('template','params'):
              
           for label in self.templ_labels:
              if x>=self.templ_labels[label].x-5 and x<=self.templ_labels[label].x+self.templ_labels[label].width \
                  and y>=self.templ_labels[label].y-10 and y<=self.templ_labels[label].y+self.templ_labels[label].height+10:
                    self._highlightedArea=label
                    print('  touched template/params ',self._highlightedArea,self.templ_labels[label].x,self.templ_labels[label].y,self.templ_labels[label].width,self.templ_labels[label].height)
                    break
           if self._highlightedArea!='':
              print('  pressed template ',self._highlightedArea,self.rotaryObj[0]['axe'])
              if '.OK' in self._highlightedArea:
                 print('  confirm template ',self._highlightedArea,self.rotaryObj[0]['axe'])
                 self._ui_confirm='OK'
                 self.enterConfirmMode()
                 self.neoIcon(text=self._ui_modes[self._ui_mode])
                  # enter in confirm mode
              self.neoHighLight(id=self._highlightedArea,labels=self.templ_labels)
           #else:
           #   self.neoPressedDrawPoint()   
        if self._highlightedArea=='' and self.debug:
            self.neoPressedDrawPoint()
        

    def refreshUiMode(self):
      self._ui_confirm='unkn'
      #print('refreshUiMode:',self.rotaryObj[0]['axe'],self._ui_modes[self._ui_mode] )
      
        
      # initRotaryStart
        
      if self._ui_modes[self._ui_mode] in ('main','drive'):
        if self._ui_mode_prev<0 or self._ui_modes[self._ui_mode_prev] not in ('main','drive'):
           if not self._ui_modes[self._ui_mode] in ('confirm'):
              self.refresh(True)
              self.labels=self.neoDrawAreas(self._msg_conf)
           
        self.neoGrid()
        self.neoLabel(self.grblParams._grbl_info,'info',hidden=False, force=True)
        if self.rotaryObj[0]['axe']!='icon' and not self._highlightedArea in ('zeroX','zeroY','zeroZ','spindeOn','spindeOff','home'):
          self.rotaryObj[0]['axe']='x'
        self.neoIcon(text=self._ui_modes[self._ui_mode])
        self.grblParams._dX2go=0.0
        self.grblParams._dY2go=0.0
        self.grblParams._dZ2go=0.0
        self.initRotaryStart()
        self.showFeed()
        # self.labels['dXY'].fgcolor=VFD_WHITE
        # self.labels['dZ'].fgcolor=VFD_WHITE

        self.show_dXY()
        self.show_dZ()
        self.show_MPG()
        self.show_coordinates()
        
        if self.rotaryObj[0]['axe']!='icon':
          self.neoHighLight(id= 'x',labels=self.labels) # default highlight x coordinate in main and drive modes
      elif self._ui_modes[self._ui_mode] in ('template','params'):
        if self._ui_mode_prev<0 or not self._ui_modes[self._ui_mode_prev] in ('template','params'):
           if not self._ui_modes[self._ui_mode] in ('confirm'):
              self.refresh(True)
              self.labels=self.neoDrawAreas(self._msg_conf)

        if self._ui_modes[self._ui_mode] in ('template'):
          try:
              self.templ_files = [ff.replace('.py','') for ff in os.listdir(self.templateDir)  if not (ff.startswith('templateGcode') or ff.startswith('_'))]
              self._current_template_idx=0
          except OSError:
              print("Error: No templates directory found.")
              self._current_template_idx=None
          #print(self.templateDir, self.templ_files)


        self.neoIcon(text=self._ui_modes[self._ui_mode]) 
        self._current_template_idx=0
        self.neoHighLight(id='term',labels=self.labels)
        
        if self._ui_modes[self._ui_mode] in ('params'):
          self.grblParserObj.queryParams()

        self.show_params()  
        self.neoLabel('','info',hidden=True, force=True)


     

    def nextUiMode(self, direction=None, to_mode=None, refresh=True):
        # print('nextUiMode:',direction,'to:',to_mode,self._ui_modes[to_mode]if to_mode is not None else None,'prev:',self._ui_mode_prev,self._ui_modes[self._ui_mode_prev])
        oldUiMode=self._ui_mode
        newMode = self._ui_mode
        if direction is not None :
          newMode+=direction
        elif to_mode is not None :
            newMode=to_mode
        if direction is None and to_mode is None: # enter in confirm mode
          newMode = len(self._ui_modes)-1 # 'confirm' mode, last element    
        elif newMode<0:
          newMode=len(self._ui_modes)-2
        elif newMode>=len(self._ui_modes)-1:
          newMode=0
        # print('nextUiMode: [3]','new:',newMode,self._ui_modes[newMode]  ,'prev:',oldUiMode,self._ui_modes[oldUiMode])
        if oldUiMode!=newMode or refresh:
          # print('nextUiMode: [4]','new:',newMode,self._ui_modes[newMode] if newMode is not None else None,'prev:',oldUiMode,self._ui_modes[oldUiMode])
          if oldUiMode is not None and self._ui_modes[oldUiMode] not in ('confirm') and oldUiMode!=newMode:
            self._ui_mode_prev=oldUiMode  
          # print('nextUiMode:[res]','prev:',self._ui_mode_prev,self._ui_modes[self._ui_mode_prev])
          self._ui_mode=newMode
          # print('nextUiMode:[res]','new:',self._ui_mode,self._ui_modes[self._ui_mode])
          self.refreshUiMode()

        



    def enterConfirmMode(self, to_mode=None, refresh=True ) :
       self.nextUiMode(direction=None,to_mode=to_mode, refresh=refresh) # enter in confirm mode


    def leave2PrevAfterConfirm(self, to_mode) :
       self.nextUiMode(direction=None,to_mode=to_mode if to_mode>=0 else 0, refresh=True) # enter in confirm mode


    def getConfirm(self):
       answ=self._ui_confirm
       self._ui_confirm='unkn'
       return answ




    def initRotaryStart(self):
        if not self._ui_modes[self._ui_mode] in ('main','drive','template','params'): # wait there for coordintes from grbl
          return 
        
        for rotObj  in self.rotaryObj:  
            if rotObj['obj'] is  None:
                continue 

            updated=False
            value = rotObj['obj'].value()
            if rotObj['axe'] in ('icon'):
              rotObj['mpos'] = self._ui_mode
              rotObj['rotary_on_mpos'] = value 
              updated=True 
            elif self._ui_modes[self._ui_mode] in ('main','drive'):
                if rotObj['axe'] in ('term'):  
                  rotObj['mpos'] = self._current_template_idx
                  rotObj['rotary_on_mpos'] = value 
                  updated=True
                elif rotObj['axe'] in ('x','y','z'):
                  rotObj['mpos'] = (self.grblParams._mX if rotObj['axe']=='x' else ( self.grblParams._mY if rotObj['axe']=='y' else self.grblParams._mZ ))
                elif rotObj['axe'] in ('dXY','dZ'): 
                  if self._ui_modes[self._ui_mode] in ('main'):
                    rotObj['mpos'] = (self._dXY_jog if rotObj['axe']=='dXY' else self._dZ_jog )
                  else:  
                    rotObj['mpos'] = (self._dXY_run if rotObj['axe']=='dXY' else self._dZ_run )
                elif rotObj['axe'] in ('mpg'):     
                   rotObj['mpos'] = 1 if self.grblParams._mpg=='1' else 0
                elif rotObj['axe'] in ('feed'):  
                  rotObj['mpos'] = (self._feedrateJog if self._ui_modes[self._ui_mode] in ('main') else self._feedrateRun )

                if self._ui_modes[self._ui_mode] in ('main'):
                  rotObj['rotary_on_mpos'] = value
                elif self._ui_modes[self._ui_mode] in ('drive'):
                  #todo minus move to block what compare
                  rotObj['rotary_on_mpos'] = value -  (self.grblParams._dX2go if rotObj['axe']=='x' else ( self.grblParams._dY2go if rotObj['axe']=='y' else self.grblParams._dZ2go ))
                updated=True

            elif self._ui_modes[self._ui_mode] in ('template','params'):
                if rotObj['axe'] in ('term'):  
                  rotObj['mpos'] = self._current_template_idx
                  rotObj['rotary_on_mpos'] = value 
                  updated=True
                elif rotObj['axe'].find('.') >=0 :
                  params=self.template.params if self._ui_modes[self._ui_mode] in ('template') else self.grblParserObj._cnc_params
                  if params is not None:
                    param=rotObj['axe'][rotObj['axe'].find('.')+1:]
                    param_val=self.get_param_by_index( params,param)
                    if param_val is not None:
                      try:
                        if isinstance(param_val, (list, tuple)):
                           v=param_val[1]
                           isFloat=param_val[1].find('.')>=0
                           if isFloat:
                              rotObj['mpos'] = float(v)
                           else:
                              rotObj['mpos'] = int(v)
                        elif isinstance(param_val, (int , float)):    
                            rotObj['mpos'] = param_val   
                        elif isinstance(param_val, (str)):    
                              v=param_val
                              isFloat=v.find('.')>=0
                              if isFloat:
                                rotObj['mpos'] = float(v)
                              else:
                                rotObj['mpos'] = int(v) 
                      except ValueError:
                              rotObj['mpos'] = 0
                    else: 
                       rotObj['mpos'] = 0        
                    rotObj['rotary_on_mpos'] = value
                    updated=True  
            if not updated:
               continue    
             
            rotObj['value_prev'] = value
            rotObj['value'] = value
            rotObj['nanosec'] = time.time_ns()
            rotObj['nanosec_prev'] = rotObj['nanosec']
        
    # link with rotary encoder  object
    def set_rotary_obj(self,rotaryObj,rotN,axe,unit):
        self.rotaryObj[rotN]={'obj':rotaryObj ,'axe':axe,'unit':unit, 
                              'state':self.state,
                              'value':rotaryObj.value(),
                              'value_prev':rotaryObj.value(),
                              'mpos':self.grblParams._mX if axe=='x' else ( self.grblParams._mY if axe=='y' else self.grblParams._mZ ),
                              'nanosec':time.time_ns(), 
                              'nanosec_prev':time.time_ns(), 
                              'rotary_on_mpos':None,
                              'scale':1.0,
                              'updated':False
                                }



    def rotary_listener(self,rotN):
        self._touched=time.ticks_ms()
        self.neoBlank(False)
        if self.rotaryObj[rotN]['obj'] is not None:
            self.rotaryObj[rotN]['value_prev']=self.rotaryObj[rotN]['value']
            self.rotaryObj[rotN]['value']=self.rotaryObj[rotN]['obj'].value()
            self.rotaryObj[rotN]['nanosec_prev']=self.rotaryObj[rotN]['nanosec']
            self.rotaryObj[rotN]['nanosec']=time.time_ns()
            self.rotaryObj[rotN]['updated']=False

    def upd_rotary_on_feed(self,rotN:int):        
        if self._ui_modes[self._ui_mode] in ('main'):    
          self._feedrateJog+=(self.rotaryObj[rotN]['value'] - self.rotaryObj[rotN]['rotary_on_mpos'])*FEED_JOG_STEPS[0]
          if self._feedrateJog<C_FEED_JOG_MIN:
              self._feedrateJog=C_FEED_JOG_MIN
          elif self._feedrateJog>C_FEED_JOG_MAX:
              self._feedrateJog=C_FEED_JOG_MAX  
        else:
          self._feedrateRun+=(self.rotaryObj[rotN]['value'] - self.rotaryObj[rotN]['rotary_on_mpos'])*FEED_RUN_STEPS[0]
          if self._feedrateRun<C_FEED_RUN_MIN:
              self._feedrateRun=C_FEED_RUN_MIN
          elif self._feedrateRun>C_FEED_RUN_MAX:
              self._feedrateRun=C_FEED_RUN_MAX  
        self.initRotaryStart()
        self.showFeed()
        self.rotaryObj[rotN]['updated'] = True

    def upd_rotary_on_mpg(self,rotN:int):  
        index_prev = 1 if self.grblParams._mpg=='1' else 0
        #print('upd_rotary_on_mpg[0]',index_prev)      
        try:
          index = index_prev
        except ValueError:
          print(f"The value {self.grblParams._mpg  } is not in the array.")
          index = 0
        index+=(1 if self.rotaryObj[rotN]['value'] - self.rotaryObj[rotN]['rotary_on_mpos']>0 else -1)
        if index>=1:
          index=1
        elif index<0:
          index=0
        if index_prev!=index:
           #print('upd_rotary_on_mpg[1]',index)      
           self.grblParserObj.toggleMPG()
        self.show_MPG() 
        self.initRotaryStart()
        self.rotaryObj[rotN]['updated'] = True

    def upd_rotary_on_icon(self,rotN:int):
        #print('upd_rotary_on_icon')  
        self.nextUiMode((1 if self.rotaryObj[rotN]['value'] - self.rotaryObj[rotN]['rotary_on_mpos']>0 else -1))
        self.rotaryObj[rotN]['updated']=True


    def upd_rotary_on_term(self,rotN:int):
        #print('upd_rotary_on_term: point1')
        if self.rotaryObj[rotN]['obj'] is None or self.rotaryObj[rotN]['rotary_on_mpos'] is None:
           return            
        #print('upd_rotary_on_term: point2')
        delta_val = self.rotaryObj[rotN]['obj'].value() - self.rotaryObj[rotN]['rotary_on_mpos']
        #print('upd_rotary_on_term: point3 delta_val=',delta_val)
        if delta_val==0 :
            return
        if self._ui_modes[self._ui_mode] == 'template': 
          #print('upd_rotary_on_term: point4 delta_val=',delta_val)
          self.termShiftPos(rotN, delta_val, self.templ_files)
          # todo self.neoDisplayTemplate(template_name ='$$')
          self.initTemplate()
          self.neoTemplateImage()
        elif self._ui_modes[self._ui_mode] == 'params':    
          self.termShiftPos(rotN, delta_val, self.grblParserObj._cnc_params)
          self.neoDisplayTemplate(template_name ='$$')
        


    def upd_rotary_on_scale_jog(self,rotN:int):        
        try:
          index = DXYZ_STEPS.index(self._dXY_jog if self.rotaryObj[rotN]['axe']=='dXY' else self._dZ_jog)
        except ValueError:
          print(f"The value {self._dXY_jog if self.rotaryObj[rotN]['axe']=='dXY' else self._dZ_jog} is not in the array.")
          index = 0
        index+=(1 if self.rotaryObj[rotN]['value'] - self.rotaryObj[rotN]['rotary_on_mpos']>0 else -1)
        if index>=len(DXYZ_STEPS):
          index=len(DXYZ_STEPS)-1
        elif index<0:
          index=0
        if self.rotaryObj[rotN]['axe']=='dXY':
          self._dXY_jog=DXYZ_STEPS[index]
          self.show_dXY() 
        else:
          self._dZ_jog=DXYZ_STEPS[index]
          self.show_dZ() 
        self.initRotaryStart()
        self.rotaryObj[rotN]['updated'] = True

    def upd_rotary_on_scale_run(self,rotN:int):        
        try:
          index = DXYZ_STEPS.index(self._dXY_run if self.rotaryObj[rotN]['axe']=='dXY' else self._dZ_run)
        except ValueError:
          print(f"The value {self._dXY_run if self.rotaryObj[rotN]['axe']=='dXY' else self._dZ_run} is not in the array.")
          index = 0
        index+=(1 if self.rotaryObj[rotN]['value'] - self.rotaryObj[rotN]['rotary_on_mpos']>0 else -1)
        if index>=len(DXYZ_STEPS):
          index=len(DXYZ_STEPS)-1
        elif index<0:
          index=0
        if self.rotaryObj[rotN]['axe']=='dXY':
          self._dXY_run=DXYZ_STEPS[index]
          self.show_dXY() 
        else:
          self._dZ_run=DXYZ_STEPS[index]
          self.show_dZ() 
        self.initRotaryStart()
        self.rotaryObj[rotN]['updated'] = True


    def termShiftPos(self,rotN, delta_val, lst):
        self.initRotaryStart()  

        if self._current_template_idx is None or len(lst)<1:
            return
        scale=1
        if abs(delta_val)>100:
           scale=10
        elif abs(delta_val)>50:
           scale=5
        elif abs(delta_val)>10:  
           scale=2

        index = self._current_template_idx + (scale if delta_val>0 else -scale)
        if index > len(lst)-1:
            self._current_template_idx=len(lst)-1
        elif index<0:
            self._current_template_idx=0
        else:
            self._current_template_idx=index
        print('termShiftPos: point5 index=',index)
        self.rotaryObj[rotN]['updated'] = True
        self.neoDraw('term', labels=self.labels, currentLine=self._current_template_idx)   



    def upd_rotary_on_main(self,rotN:int):    
        if self.rotaryObj[rotN]['value'] is None or self.rotaryObj[rotN]['rotary_on_mpos'] is None:
           return
        delta_val = self.rotaryObj[rotN]['value'] - self.rotaryObj[rotN]['rotary_on_mpos']
        if delta_val==0 :
            return
        if self.rotaryObj[rotN]['axe']=='x':
            step = delta_val *  self._dXY_jog
            self.grblJog(x=step, feedrate=self._feedrateJog)
        elif self.rotaryObj[rotN]['axe']=='y':
            step = delta_val *  self._dXY_jog
            self.grblJog(y=step, feedrate=self._feedrateJog)
        elif self.rotaryObj[rotN]['axe']=='z':
            step = delta_val * self._dZ_jog
            self.grblJog(z=step, feedrate=self._feedrateJog)  
        elif self.rotaryObj[rotN]['axe'] in( 'dXY', 'dZ'):
            self.upd_rotary_on_scale_jog(rotN)
        elif self.rotaryObj[rotN]['axe'] in( 'feed' ):
          self.upd_rotary_on_feed(rotN) 
        elif self.rotaryObj[rotN]['axe'] in( 'mpg' ):
          self.upd_rotary_on_mpg(rotN)


    def get_param_by_index(self,params,param_name:str):
        if isinstance(params, dict) :
          if param_name in params:    
            return params[param_name]
        elif isinstance(params, (list, tuple)) :
            index=-1
            for i in range(len(params)):  
                if params[i][0]==param_name or (param_name.startswith('$') and '$$.'+params[i][0]== param_name ) :
                    index=i
                    break
            if index>=0 and len(params[index])>=2:
               return params[index]
        return None


    def upd_rotary_on_drive(self,rotN:int):
        if self.rotaryObj[rotN]['value'] is None or self.rotaryObj[rotN]['rotary_on_mpos'] is None:
           return            
        delta_val = self.rotaryObj[rotN]['value'] - self.rotaryObj[rotN]['rotary_on_mpos']
        if delta_val==0 :
            return
        #step = delta_val * self.rotaryObj[rotN]['unit'] *  self.rotaryObj[rotN]['scale']

        if self.rotaryObj[rotN]['axe']=='x':
            #self.grblJog(x=step, feedrate=self._feedrateRun)
            self.grblParams._dX2go=delta_val *self._dXY_run
            self.show_coordinates('x')
            self.rotaryObj[rotN]['updated'] = True
            # print('new pos x',self.grblParams._dX2go)
        elif self.rotaryObj[rotN]['axe']=='y':
            self.grblParams._dY2go=delta_val *self._dXY_run
            self.rotaryObj[rotN]['updated'] = True
            self.show_coordinates('y')
            # print('new pos y' ,self.grblParams._dY2go)
        elif self.rotaryObj[rotN]['axe']=='z':
            self.grblParams._dZ2go=delta_val * self._dZ_run
            self.rotaryObj[rotN]['updated'] = True
            self.show_coordinates('z')
            # print('new pos z', self.grblParams._dZ2go)
        elif self.rotaryObj[rotN]['axe'] in( 'dXY', 'dZ'):
            self.upd_rotary_on_scale_run(rotN)
        elif self.rotaryObj[rotN]['axe'] in( 'feed' ):
          self.upd_rotary_on_feed(rotN) 
            
    def upd_rotary_on_template(self,rotN:int,params:dict):
        if params is  None:
           return
        if self.rotaryObj[rotN]['obj'] is None or self.rotaryObj[rotN]['rotary_on_mpos'] is None:
           return            
        delta_val = self.rotaryObj[rotN]['obj'].value() - self.rotaryObj[rotN]['rotary_on_mpos']
        if delta_val==0 :
            return
        elif self.rotaryObj[rotN]['axe'].find('.') >=0:
          param=self.rotaryObj[rotN]['axe'][self.rotaryObj[rotN]['axe'].find('.')+1:]
          param_val=self.get_param_by_index(params,param)
          if param_val is not None:
            scale=1.0
            val=None
            if isinstance(param_val, (list, tuple)):
              v=param_val[1]
              isFloat=param_val[1].find('.')>=0
              if isFloat:
                if len(v)-v.find('.')-1>=2 and float(v)<10.0:
                    scale=0.01
                elif len(v)-v.find('.')-1>=1:
                    scale=0.1
                val=float(v)+delta_val*scale
              else:
                val=int(v)+int(delta_val*scale)
              param_val[1]=str(val)
              print('update param',param,' to ',param_val[1], param)  
            else:
              val= param_val+delta_val*scale 
              params[param]=val
            if val is not None:
              print('res update params=',params,' param= ',param,' val ',val)  
              self.initRotaryStart() 
              self.templ_labels[self.rotaryObj[rotN]['axe']].text=('{0:.2f}' if scale <0.1 else '{0:.1f}').format(val)
              self.neoDraw(self.rotaryObj[rotN]['axe'], labels=self.templ_labels)
                        


 
     


    def showFeed(self) :     
        if self._ui_modes[self._ui_mode] in ('main','feedJog'):
          text='{:4.0f}'.format(self._feedrateJog)
        else:
          text='{:4.0f}'.format(self._feedrateRun)
        self.neoLabel(text,id='feed')

    def show_dXY(self) :
     if self._ui_modes[self._ui_mode] =='main' :
        if self._dXY_jog<1.0:    
           self.neoLabel('{:4.2f}'.format(self._dXY_jog),id='dXY')
        else:
           self.neoLabel('{:4.0f}'.format(self._dXY_jog),id='dXY')
     else:
        if self._dXY_run<1.0:    
           self.neoLabel('{:4.2f}'.format(self._dXY_run),id='dXY')
        else:
           self.neoLabel('{:4.0f}'.format(self._dXY_run),id='dXY')      
             
         
    def show_dZ(self) :
      if self._ui_modes[self._ui_mode] =='main' :       
        if self._dZ_jog<1.0: 
          self.neoLabel('{:4.2f}'.format(self._dZ_jog),id='dZ')
        else:
          self.neoLabel('{:4.0f}'.format(self._dZ_jog),id='dZ')
      else:
        if self._dZ_run<1.0: 
          self.neoLabel('{:4.2f}'.format(self._dZ_run),id='dZ')
        else:
          self.neoLabel('{:4.0f}'.format(self._dZ_run),id='dZ') 
             

 


    def neoTerm(self,text,color=None, currentLine=None,hidden=None) :   
        self.neoLabel(text,id='term',color=WHITE if color is None else  color,currentLine=currentLine,hidden=hidden )  


    def neoTermInfo(self,command) :   
      #print("neoTerm",command,text)  
      if command=='termLineUp': 
          self.decTermLinePos()
      elif command=='termLineDown' : 
          self.incTermLinePos()
      elif command=='termLineLeft' : 
          self.decTermPos()
      elif command=='termLineRight' : 
          self.incTermPos()
      elif command=='termHome' : 
          self.homeTermPos()
      if len(self.grblParams._grbl_info)>0:
        self.neoLabel(self.grblParams._grbl_info,id='term',color=WHITE )        
       
    def inc_feedrateJog(self):
      if self._feedrateJog+100.0 > C_FEED_JOG_MAX:
           self._feedrateJog = C_FEED_JOG_MAX
      else:    
           self._feedrateJog +=100.0
      self.grblParams._state_prev='feed'
      #print('g_feedrate now',self._feedrate)  


    def dec_feedrateJog(self):
      if self._feedrateJog-100.0 < C_FEED_JOG_MIN:
           self._feedrateJog = C_FEED_JOG_MIN
      else:    
           self._feedrateJog -=100.0
      self.grblParams._state_prev='feed'     
      #print('g_feedrate now',self._feedrate)  


    def inc_feedrateRun(self):
      if self._feedrateRun+100.0 > C_FEED_JOG_MAX:
           self._feedrateRun = C_FEED_JOG_MAX
      else:    
           self._feedrateRun +=100.0
      self.grblParams._state_prev='feed'
      #print('g_feedrate now',self._feedrate)  


    def dec_feedrateRun(self):
      if self._feedrateRun-100.0 < C_FEED_JOG_MIN:
           self._feedrateRun = C_FEED_JOG_MIN
      else:    
           self._feedrateRun -=100.0
      self.grblParams._state_prev='feed'     
      #print('g_feedrate now',self._feedrate)        

    def inc_stepXY(self):
      if self._dXY_jog*10.0>C_STEP_MAX:
           self._dXY_jog =C_STEP_MAX
      else:   
           self._dXY_jog *=10.0
      self.grblParams._state_prev='stepX'     
      #print('g_step+ now',self._dXY)         

    def dec_stepXY(self):
      if self._dXY_jog*0.1<C_STEP_MIN:
           self._dXY_jog =C_STEP_MIN
      else:   
           self._dXY_jog *=0.1
      self.grblParams._state_prev='stepX'          
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
      self._dXY_jog=self.nextStepVals(self._dXY_jog,DXYZ_STEPS)
      self.grblParams._state_prev='stepX'          
      #print('g_step _dXY now',self._dXY)     

    def stepZ(self):
      self._dZ_jog=self.nextStepVals(self._dZ_jog,DXYZ_STEPS)
      self.grblParams._state_prev='stepZ'          
      #print('g_step _dZ now',self._dZ)     

    def set_feedrate(self):
      self._feedrateJog=self.nextStepVals(self._feedrateJog, FEED_JOG_STEPS)
      self.grblParams._state_prev='feed'          
      #print('g_feedrate now',self._feedrate) 


    def inc_stepZ(self):
      if self._dXY_jog*10.0>C_STEP_Z_MAX:
           self._dZ_jog =C_STEP_Z_MAX
      else:   
           self._dZ_jog *=10.0
      self.grblParams._state_prev='stepZ'          
      #print('g_step_z now',self._dZ)         

    def dec_stepZ(self):
      if self._dZ_jog*0.1<C_STEP_Z_MIN:
           self._dZ_jog =C_STEP_Z_MIN
      else:   
           self._dZ_jog *=0.1
      self.grblParams._state_prev='stepZ'          
      #print('g_step_z now',self._dZ)  

    def set_jog_arrow(self, arrow:str, val):
      #print('new set_jog_arrow ',arrow)
      self._jog_arrow = arrow
      self._jog_value = val

    def setEdit(self, text):
       self._editCmd=text

    # task every 1s
    def upd_rotary(self):
        
        for rotN in range(len(self.rotaryObj)):
            if self.rotaryObj[rotN]['obj'] is not None  :
                if self.rotaryObj[rotN]['updated'] and \
                  (self._ui_modes[self._ui_mode] == 'drive' or self._ui_modes[self._ui_mode] in ('template','params') or self.rotaryObj[rotN]['axe'] in ('icon','term') or self.rotaryObj[rotN]['axe'] in ('dXY','dZ','feed')): 
                  continue
                

                #print ('upd_rotary: every 1s[2], rotN=',rotN, self.rotaryObj[rotN]['state'], self.rotaryObj[rotN]['value'],self.rotaryObj[rotN]['axe'])
                if self.rotaryObj[rotN]['state'] not in ('jog','run','planed'):
                    #print ('upd_rotary: every 1s[3], rotN=',rotN, time.time_ns()-self.rotaryObj[rotN]['nanosec'],time.time_ns(),self.rotaryObj[rotN]['nanosec'])
                    if self.rotaryObj[rotN]['value'] is None or self.rotaryObj[rotN]['rotary_on_mpos'] is None or self.rotaryObj[rotN]['nanosec'] is None:
                       continue                    
                    if time.time_ns()-self.rotaryObj[rotN]['nanosec'] < PENDANT_READ_INTERVAL:
                       #print ('upd_rotary: scip when wheeling')
                       continue
                    if self.rotaryObj[rotN]['value'] == self.rotaryObj[rotN]['rotary_on_mpos'] :
                       #print ('upd_rotary: scip when value not changed')
                       continue
                    #print ('upd_rotary: every 1s[4], rotN=',rotN,'axe',self.rotaryObj[rotN]['axe'],   self.rotaryObj[rotN]['state'], self.rotaryObj[rotN]['value'],'mode',self._ui_modes[self._ui_mode])
                    if self.rotaryObj[rotN]['axe'] in ('icon') :
                       self.upd_rotary_on_icon(rotN)
                    elif self.rotaryObj[rotN]['axe'] in ('term') :
                       self.upd_rotary_on_term(rotN)   
                    elif self._ui_modes[self._ui_mode] == 'main':
                      self.upd_rotary_on_main(rotN)
                    elif self._ui_modes[self._ui_mode] == 'drive':
                      self.upd_rotary_on_drive(rotN)
                    elif self._ui_modes[self._ui_mode] == 'template':
                      self.upd_rotary_on_template(rotN,self.template.params)
                    elif self._ui_modes[self._ui_mode] == 'params':
                      self.upd_rotary_on_template(rotN,self.grblParserObj._cnc_params)

                    
                          

                     



# G10L20P1Y0 bCNC set wpos g54(p1) for y = 0    https://linuxcnc.org/docs/html/gcode/g-code.html#gcode:g10-l2 
# G10 L20 is similar to G10 L2 except that instead of setting the offset/entry to the given value, it is set to a calculated value that makes the current coordinates become the given value.                   
#<Idle|MPos:14.000,31.000,8.000,0.000|Bf:100,1023|FS:0,0|Pn:P|WCO:0.000,31.000,6.000,0.000>
#MPos:14.000,31.000,8.000
#  minus
#  WCO:0.000,31.000,6.000
#WPOS:14.000,0.000,2.000