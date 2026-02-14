import time

from nanoguilib.writer import CWriter
from nanoguilib.meter import Meter
from nanoguilib.label import Label, ALIGN_LEFT, ALIGN_RIGHT, ALIGN_CENTER 
from nanoguilib.textbox import Textbox

# Fonts
import nanoguilib.arial10 as arial10
import nanoguilib.courier20 as fixed
import nanoguilib.arial35 as arial35


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

DEBUG= False

class NeoLabelObj(object):
    def __init__(self, fgcolor:int , scale:float,x:int,y:int,text:str = '',label=None,fldLabel=None,
                 oneWidth:int=20, nlines:int=1, align = ALIGN_LEFT, bdcolor=None, invert=False, hidden = False):
        self.x= x
        self.y= y
        self.text=  text
        self.scale= scale
        self.fgcolor= fgcolor
        self.bdcolor= bdcolor
        self.invert= invert
        self.nlines = nlines  
        self.label= label
        self.width= self.label.width
        self.height= self.label.height
        self.oneWidth= oneWidth
        self.charsl=5
        self.hidden = hidden
        self.align =  align
        self.chars = 5
        if self.width is not None and self.oneWidth is not None and self.oneWidth>0 and self.width>0 :
          # self.charsl=self.width//self.oneWidth + (1 if (self.width%self.oneWidth)>0 else 0)
          self.charsl=self.width//self.oneWidth 
          self.chars =self.charsl * self.nlines
        
        self.fldLabel = fldLabel

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


class Gui(object ):

    _jog_arrow:str = ''
    _jog_value:float = 0.0
    _highlightedArea:str= 'x'
    _pressedX:int= None
    _pressedY:int= None
    _pressedOldX:int= None
    _pressedOldY:int= None
    rotaryObj=[{'obj':None ,'axe':'x','unit':1.0, 'value':0,'value_prev':0,'mpos':0,'nanosec':0, 'scale':1.0 },
               {'obj':None ,'axe':'y','unit':1.0, 'value':0,'value_prev':0,'mpos':0,'nanosec':0, 'scale':1.0 }]

    #_ui_modes=['main','drive','feedJog','feedRun','scaleXY','scaleZ','confirm'] #confirm must be last
    _ui_modes=['main','drive','confirm'] #confirm must be last
    _ui_mode=0
    _ui_confirm='unkn'
    _ui_mode_prev=0
    _dXY:float = DXYZ_STEPS[2]
    _dZ:float = DXYZ_STEPS[2]
    _feedrateJog:float =  FEED_JOG_STEPS[2]
    _feedrateRun:float =  FEED_JOG_STEPS[2]

    term_line_from:int = 1
    term_pos_from:int = 0    
    _editCmd:str = ''

    neo_refresh:bool = False

    debug:bool = DEBUG
    enable_invert_on_select = True


    def __init__(self, neo, grblParams,
                  grblParserObj,
                  debug:bool = DEBUG):
       
       self.neo=neo
       self.grblParams=grblParams
       self.grblParserObj=grblParserObj
       self.debug=debug
       self.neoInit()
       #self.hello()
       

    @property
    def state(self):
        return self.grblParams._state


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
       

                 
    # initialize neo display labels
    def neoInit(self):
        self._msg_conf = [
            ('x', '     '        , X_ARROW_COLOR   ,  150,  35,  3, 126    ,1, ALIGN_RIGHT), #9*14
            ('y', '     '        , Y_ARROW_COLOR   ,  150, 115,  3, 126    ,1, ALIGN_RIGHT),
            ('z', '     '        , Z_ARROW_COLOR   ,  150, 195,  3, 126    ,1, ALIGN_RIGHT),
            ('mx', '     '       , X_ARROW_COLOR   ,  150+67,  35+40,  2, 126    ,1, ALIGN_RIGHT), #9*14
            ('my', '     '       , Y_ARROW_COLOR   ,  150+67, 115+40,  2, 126    ,1, ALIGN_RIGHT),
            ('mz', '     '       ,Z_ARROW_COLOR    ,  150+67, 195+40,  2, 126    ,1, ALIGN_RIGHT),
            ('dXY', 'dXY'        , Y_ARROW_COLOR   ,  150-10, (115-35)//2+35+10,  2, 60    ,1, ALIGN_RIGHT),
            ('dZ', 'dZ'          , Z_ARROW_COLOR   ,  150-10, 195+40 ,  2, 60    ,1, ALIGN_RIGHT),
            ('cmd', '     '      , 'white'         ,    0, 260,  2, 308    ,1, ALIGN_LEFT),  #14*22
            ('feed', '1000'    , 'white'   ,  0,  0,  2, 6*15-1,1, ALIGN_LEFT),
            ('state', 'Idle MPG G59'    , 'white'         ,  6*20,  0,  2, 310-120,1, ALIGN_LEFT),
            ('term', 'F1 - Help' , 'white'         ,             0,  40,  2, 140          ,10, ALIGN_LEFT),
            ('<', '<< '           ,  'yellow'       ,   10, 400,  3, 60     ,1, ALIGN_LEFT),
            ('icon', self._ui_modes[self._ui_mode] , ICON_COLOR, 20+3*14,  405, 2, 250-20-3*14    ,1, ALIGN_CENTER),
            ('>', ' >>'           ,  'lblue'        ,  250, 400,  3, 60     ,1, ALIGN_LEFT),
            ('info', 'info'      , 'white'         ,    0, 280,  2, 306    ,4, ALIGN_LEFT)  #6*51
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
            (name, textline, fgcolor, x, y, scale, width, nlines,align ) = c1  # unpack tuple into five var names
            fgcolor = color2rgb(fgcolor)
            fnt=arial35 if scale==3 else (arial10 if scale==1 else fixed)
            writer = CWriter(self.neo, fnt, verbose=self.debug)
            writer.set_clip(False, False, False) #row_clip=None, col_clip=None, wrap=None


            if name in ('xyz'):
              self.neo.rect(x+5,y+5,10,10,VFD_WHITE,True)
              flw=writer.stringlen(name.upper()+': ')
              fl=Label(writer, y, x, flw,fgcolor=fgcolor)
              fl.value(name.upper()+': ',fgcolor=fgcolor)
              ll=Label(writer, y, x+flw, writer.stringlen('-999.99'), bdcolor=False, align=align)
              ll.value('{:6.2f}'.format(-123.01), fgcolor=VFD_WHITE)
              
              self.labels[name] = NeoLabelObj(text  = textline, fgcolor=VFD_WHITE, bdcolor=False , align=align, scale=scale,x=x,y=y,label=ll,fldLabel=fl, oneWidth=writer.stringlen('0'))
            elif name in ('mx','my','mz'):
              ll=Label(writer, y, x, writer.stringlen('-999.99'), bdcolor=False, align=align)
              ll.value('{:6.2f}'.format(-456.02), fgcolor=VFD_WHITE)
              
              self.labels[name] = NeoLabelObj(text  = textline, fgcolor=VFD_WHITE , bdcolor=False, align=align, scale=scale,x=x,y=y,label=ll,fldLabel=fl, oneWidth=writer.stringlen('0'))

            elif name in ('state'):
              ll=Label(writer, y, x, width,fgcolor=fgcolor,bgcolor=VFD_BG, align=align)
              if textline.strip()!='':
                  ll.value(textline,fgcolor=fgcolor, align=align)
              else:    
                ll.value(name,fgcolor=fgcolor, align=align)
              self.labels[name] = NeoLabelObj(text  = textline, fgcolor=fgcolor ,  bdcolor=False, align=align , scale=scale,x=x,y=y,label=ll,oneWidth=writer.stringlen('0'))
            elif name in ('dXY','dZ'):
              ll=Label(writer, y, x, width,fgcolor=fgcolor,bgcolor=VFD_BG, align=align)
              textline = '{:4.0f}'.format(self._dXY if name in ('dXY') else self._dZ)
              ll.value(textline, fgcolor=VFD_WHITE)
              self.labels[name] = NeoLabelObj(text  = textline, fgcolor=fgcolor ,  bdcolor=False, align=align , scale=scale,x=x,y=y,label=ll,oneWidth=writer.stringlen('0'))              
            elif name in ('feed'):
              ll=Label(writer, y, x, width,fgcolor=fgcolor,bgcolor=VFD_BG, align=align)
              textline='{:4.0f}'.format(self._feedrateJog)
              ll.value(textline,fgcolor=fgcolor, align=align)
              self.labels[name] = NeoLabelObj(text  = textline, fgcolor=fgcolor ,  bdcolor=False, align=align , scale=scale,x=x,y=y,label=ll,oneWidth=writer.stringlen('0'))
            elif name in ('cmd','icon'):
              ll=Label(writer, y, x, width,fgcolor=fgcolor,bgcolor=VFD_BG, align=align)
              if textline.strip()!='':
                  ll.value(textline,fgcolor=fgcolor, align=align)
              else:    
                ll.value(name, align=align)
              self.labels[name] = NeoLabelObj(text  = textline, fgcolor=fgcolor ,  bdcolor=False, align=align , scale=scale,x=x,y=y,label=ll,oneWidth=writer.stringlen('0'))
            elif name in ('info','term'):
              ll=Textbox(writer, clip=False, row=y, col=x, width=width, nlines=nlines, bdcolor=False, fgcolor=fgcolor,bgcolor=VFD_BG)
              if textline.strip()!='':
                  ll.append(textline)
              self.labels[name] = NeoLabelObj(text  = textline, fgcolor=fgcolor , align=align , scale=scale,x=x,y=y,nlines=nlines,label=ll,oneWidth=writer.stringlen('0'))
            else: # etc
              ll=Label(writer, y, x, width,fgcolor=fgcolor,bgcolor=VFD_BG, align=align)
              if textline.strip()!='':
                  ll.value(textline,fgcolor=fgcolor, align=align)
              else:    
                ll.value(name,fgcolor=fgcolor, align=align)
              self.labels[name] = NeoLabelObj(text  = textline, fgcolor=fgcolor , align=align , scale=scale,x=x,y=y,label=ll,oneWidth=writer.stringlen('0'))
        self.neoHighLight(id=self._highlightedArea)
        self.neo_refresh= True


    # ui label`s updater
    def neoLabel(self,text,id='info',color=None):
        
        color = color2rgb(color)
        l_id=id
        if id=='x':
          self.labels[id].text = text
        elif id=='y': 
          self.labels[id].text = text
        elif id=='z':
          self.labels[id].text = text
        elif id=='mx':
          self.labels[id].text = text
        elif id=='my': 
          self.labels[id].text = text
        elif id=='mz':
          self.labels[id].text = text  
        elif id=='cmd':
          self.labels[id].text = text
          if color is None:
             self.labels[id].fgcolor=VFD_YELLOW
        elif id=='state':
          self.labels[id].text = text+(' MPG' if self.grblParams._mpg else '   ')+(' '+self.grblParams._wcs if self.grblParams._wcs is not None else  '    ')
          if color is None and text.lower().startswith('alarm'):
             self.labels[id].fgcolor=VFD_RED
          elif color is None and (text.lower().startswith('run') or text.lower().startswith('jog')):
             self.labels[id].fgcolor=VFD_GREEN
          elif color is None:
             self.labels[id].fgcolor=VFD_WHITE
          else:   
             self.labels[id].fgcolor=color
        elif id=='feed':
          self.labels[id].text = text
          if color is None and text.lower().startswith('alarm'):
             self.labels[id].fgcolor=VFD_RED
          elif color is None and (text.lower().startswith('run') or text.lower().startswith('jog')):
             self.labels[id].fgcolor=VFD_GREEN
          elif color is None:
             self.labels[id].fgcolor=VFD_WHITE
          else:   
             self.labels[id].fgcolor=color             
        elif id=='icon':
          self.labels['term'].hidden=(len(text.strip())>2)
          self.labels[id].text = text
          if color is None:
             self.labels[id].fgcolor=VFD_GREEN
          else:   
             self.labels[id].fgcolor=color

        elif id=='term':
          self.labels[id].text = text
          if color is None:
             self.labels[id].fgcolor=VFD_GREEN
          else:   
             self.labels[id].fgcolor=color
        elif id=='info':
          self.labels[id].text = text
          if color is None:
             self.labels[id].fgcolor=VFD_LBLUE if self.grblParams._mpg  else VFD_WHITE
          else:   
             self.labels[id].fgcolor=color
        elif id in ('dXY','dZ'):
          self.labels[id].text = text
          if color is not None:
             self.labels[id].fgcolor=color
          elif color is None and ((self._ui_modes[self._ui_mode] == 'scaleZ' and id=='dZ') or (self._ui_modes[self._ui_mode] == 'scaleXY' and id=='dXY')):
             self.labels[id].fgcolor=VFD_YELLOW 
          else:
             self.labels[id].fgcolor=VFD_WHITE
             
        else:
            l_id=None
        self.neoDraw(l_id)     

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
            self.neo.rect(self._pressedX-5,self._pressedY-5,10,10,VFD0_WHITE,True)
            self.neo_refresh= True

    # draw/update neo display label    
    def neoDraw(self,id):
        if id is not None:
            if DEBUG:
                print('neoDraw['+id+']',self.labels[id].x,self.labels[id].y,self.labels[id].fgcolor,self.labels[id].text)
            if isinstance(self.labels[id].label,Textbox )  :
              if self.labels[id].invert:
                self.labels[id].label.bdcolor=VFD_LBLUE
              else:
                self.labels[id].label.bdcolor=False  
              self.labels[id].label.clear()
              self.labels[id].label.fgcolor=self.labels[id].fgcolor
              # self.labels[id].label.append(self.labels[id].text)
              self.labels[id].label.append(self.labels[id].text[ : self.labels[id].chars])
              
              self.labels[id].label.goto(0)
            else:   
              if self.labels[id].charsl-len(self.labels[id].text)>0  and (self.labels[id].align is None or self.labels[id].align==ALIGN_LEFT) :
                  self.labels[id].label.value( self.labels[id].text + ( " " * (self.labels[id].charsl + (1 if id not in('xyz') else 0)  - len(self.labels[id].text) ))   ,fgcolor=self.labels[id].fgcolor, align=self.labels[id].align, invert=self.labels[id].invert,bdcolor=self.labels[id].bdcolor)
              else:    
                self.labels[id].label.value(self.labels[id].text[:self.labels[id].charsl],fgcolor=self.labels[id].fgcolor, align=self.labels[id].align, invert=self.labels[id].invert,bdcolor=self.labels[id].bdcolor)
            
            self.neo_refresh= True

    def getHelp(self):
       self.helpIdx+=1
       self.helpIdx=self.helpIdx%len(self.help)
       return self.help[self.helpIdx]
       

    def neoIcon(self,text,color=None) :     
        self.neoLabel(text,id='icon',color=color2rgb(ICON_COLOR) if color is None else  color)            



    @property
    def step(self):
        return self._dXY          

    @property
    def stepdZ(self):
        return self._dZ          

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

    def neoMachineCoordinate(self, id:str):
        self.neoLabel('{0:.2f}'.format(getattr(self.grblParams, '_m' + id.upper())), id='m' + id)


    def displayState(self):     

      #self.parseState(grblState)
      # print("MPG ->",grblState,' \n - >> prev ',self.state_prev, self.mpg_prev,' now=>',self.state, self.mpg)
      self.neoLabel(self.grblParams._grbl_display_state,id='info')
      
      if len(self.grblParams._grbl_info)>0:
         self.neoTerm(self.grblParams._grbl_info)

      self.neoWorkCoordinate(id='x')
      self.neoWorkCoordinate(id='y')
      self.neoWorkCoordinate(id='z')

      self.neoMachineCoordinate(id='x')
      self.neoMachineCoordinate(id='y')
      self.neoMachineCoordinate(id='z')
      
      
      
      
      
      
      if self.mpg is not None and (self.mpg_prev is None or self.mpg !=self.mpg_prev):
          self.grblParams._mpg_prev=self.grblParams._mpg
      if self.grblParserObj.state_is_changed() or self.state == 'idle' or self.state.startswith('hold') :  
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


    def neoHighLight(self,id):
        if id in self.labels:
              if not self.labels[id].invert:
                  self.labels[id].invert = True
                  self.labels[id].label.show()
                  if id in ('x','y','z','dXY','dZ','feed') and self.rotaryObj[0]['axe']!=id:
                    self.rotaryObj[0]['axe'] = id
                    if id in ('x','y','z'):
                      self.neoWorkCoordinate(id=id)
                    self.initRotaryStart()

                  self.neoDraw(id)
              for label in self.labels:
                  if label!=id:
                    if  self.labels[label].invert :
                        self.labels[label].invert = False
                        if id in ('x','y','z'):
                            self.neoWorkCoordinate(id=id)
                        self.neoDraw(label)
              self.neo_refresh =True          

    def touchscreen_press(self,x, y):
        # print('touchscreen_press:',x,y)  
        self._highlightedArea=''
        self._pressedOldX = self._pressedX
        self._pressedOldY = self._pressedY  
        self._pressedX = x
        self._pressedY = y
        
        

        for label in self.labels:
            if label in ('x','y','z','<','>','term','dXY','dZ','feed'):
               ll=self.labels[label]
               if x>=ll.x-2 and x<=ll.x+ll.width+2 and y>=ll.y-2 and y<=ll.y+ll.height+2:
                   self._highlightedArea=label
                   break
        if self._highlightedArea=='':
          self.neoPressedDrawPoint()
        else:         
          print('  pressed ',self._highlightedArea)
          self.neoHighLight(id=self._highlightedArea)
          if self._highlightedArea in ('<','>'):
             self.nextUiMode(-1 if self._highlightedArea in ('<') else 1)

            #elif self._pressedArea in ('x','y','z'):
            # if self.enable_invert_on_select:    
            #     if not self.labels[self._pressedArea].invert:
            #       self.labels[self._pressedArea].invert=True
            #       self.labels[self._pressedArea].label.show()
            #       if self.rotaryObj[0]['axe']!=self._pressedArea:
            #           self.rotaryObj[0]['axe'] = self._pressedArea
            #           self.neoWorkCoordinate(id=self._pressedArea)
            #           self.initRotaryStart()
            #       if self._pressedArea!='x' and self.labels['x'].invert:
            #           self.labels['x'].invert=False
            #           self.labels['x'].label.show()
            #           self.neoWorkCoordinate(id='x')
            #       if self._pressedArea!='y' and self.labels['y'].invert:
            #           self.labels['y'].invert=False
            #           self.labels['y'].label.show()
            #           self.neoWorkCoordinate(id='y')
            #       if self._pressedArea!='z' and self.labels['z'].invert:
            #           self.labels['z'].invert=False
            #           self.labels['z'].label.show()
            #           self.neoWorkCoordinate(id='z')
            # else:       
            #     if self.labels[self._pressedArea].fgcolor!=VFD_YELLOW:
            #       self.labels[self._pressedArea].fgcolor=VFD_YELLOW
            #       if self.rotaryObj[0]['axe']!=self._pressedArea:
            #           self.rotaryObj[0]['axe'] = self._pressedArea
            #           self.neoWorkCoordinate(id=self._pressedArea)
            #           self.initRotaryStart()
            #       if self._pressedArea!='x' and self.labels['x'].fgcolor!=VFD_LBLUE:
            #           self.labels['x'].fgcolor=VFD_LBLUE
            #           self.neoWorkCoordinate(id='x')
            #       if self._pressedArea!='y' and self.labels['y'].fgcolor!=VFD_LBLUE:
            #           self.labels['y'].fgcolor=VFD_LBLUE
            #           self.neoWorkCoordinate(id='y')
            #       if self._pressedArea!='z' and self.labels['z'].fgcolor!=VFD_LBLUE:
            #           self.labels['z'].fgcolor=VFD_LBLUE
            #           self.neoWorkCoordinate(id='z')
            

    def nextUiMode(self, direction):
        self._ui_mode+=direction
        if direction==0: # enter in confirm mode
          self._ui_mode_prev=self._ui_mode
          self._ui_mode = len(self._ui_modes)-1 # 'confirm' mode, last element    
        elif self._ui_mode<0:
          self._ui_mode=len(self._ui_modes)-2
        elif self._ui_mode>=len(self._ui_modes)-1 or self._ui_modes[self._ui_mode]=='confirm':
          self._ui_mode=0

        self._ui_confirm='unkn'
        self.neoIcon(text=self._ui_modes[self._ui_mode])
        self.initRotaryStart()
        self.showFeed()
        self.labels['dXY'].fgcolor=VFD_WHITE
        self.labels['dZ'].fgcolor=VFD_WHITE

        self.showdXY()
        self.showdZ()

    def enterConfirmMode(self):
       self.nextUiMode(0)


    def getConfirm(self):
       answ=self._ui_confirm
       self._ui_confirm='unkn'
       return answ




    def initRotaryStart(self):
        if not self._ui_modes[self._ui_mode] in ('main','drive'): # wait there for coordintes from grbl
          return 
        
        for rotObj  in self.rotaryObj:  
            if rotObj['obj'] is  None:
                continue 

            updated=False
            if self._ui_modes[self._ui_mode] in ('main','drive'):
                if rotObj['axe'] in ('x','y','z'):
                  rotObj['mpos'] = (self.grblParams._mX if rotObj['axe']=='x' else ( self.grblParams._mY if rotObj['axe']=='y' else self.grblParams._mZ ))
                elif rotObj['axe'] in ('dXY','dZ'):  
                  rotObj['mpos'] = (self._dXY if rotObj['axe']=='dXY' else self._dZ )
                elif rotObj['axe'] in ('feed'):  
                  rotObj['mpos'] = (self._feedrateJog if self._ui_modes[self._ui_mode] in ('main') else self._feedrateRun )
                updated=True
            elif self._ui_modes[self._ui_mode] in ('feedJog'):
                rotObj['mpos'] = self._feedrateJog
                updated=True
            elif self._ui_modes[self._ui_mode] in ('feedRun'):
                rotObj['mpos'] = self._feedrateRun
                updated=True
            if not updated:
               continue    
               
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
                              'mpos':self.grblParams._mX if axe=='x' else ( self.grblParams._mY if axe=='y' else self.grblParams._mZ ),
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


    def upd_rotary_on_main(self,rotN:int):    
        if self.rotaryObj[rotN]['value'] is None or self.rotaryObj[rotN]['rotary_on_mpos'] is None:
           return
        delta_val = self.rotaryObj[rotN]['value'] - self.rotaryObj[rotN]['rotary_on_mpos']
        if delta_val==0 :
            return

        #step = delta_val * self.rotaryObj[rotN]['unit'] *  self.rotaryObj[rotN]['scale']
        
        if self.rotaryObj[rotN]['axe']=='x':
            step = delta_val *  self._dXY
            self.grblJog(x=step, feedrate=self._feedrateJog)
        elif self.rotaryObj[rotN]['axe']=='y':
            step = delta_val *  self._dXY
            self.grblJog(y=step, feedrate=self._feedrateJog)
        elif self.rotaryObj[rotN]['axe']=='z':
            step = delta_val * self._dZ
            self.grblJog(z=step, feedrate=self._feedrateJog)  
        elif self.rotaryObj[rotN]['axe'] in( 'dXY', 'dZ'):
            try:
              index = DXYZ_STEPS.index(self._dXY if self.rotaryObj[rotN]['axe']=='dXY' else self._dZ)
            except ValueError:
              print(f"The value {self._dXY if self.rotaryObj[rotN]['axe']=='dXY' else self._dZ} is not in the array.")
              index = 0
            print(' index1',index)  
            index+=(1 if delta_val>0 else -1)
            print(' index2',index)  
            if index>=len(DXYZ_STEPS):
              index=len(DXYZ_STEPS)-1
            elif index<0:
              index=0
            print(' index3',index,DXYZ_STEPS[index])  
            if self.rotaryObj[rotN]['axe']=='dXY':
              self._dXY=DXYZ_STEPS[index]
              self.showdXY() 
            else:
              self._dZ=DXYZ_STEPS[index]
              self.showdZ() 
            self.initRotaryStart()
        elif self.rotaryObj[rotN]['axe'] in( 'feed' ): 
          if self._ui_modes[self._ui_mode] in ('main'):    
            self._feedrateJog+=delta_val*FEED_JOG_STEPS[0]
            if self._feedrateJog<C_FEED_JOG_MIN:
                self._feedrateJog=C_FEED_JOG_MIN
            elif self._feedrateJog>C_FEED_JOG_MAX:
                self._feedrateJog=C_FEED_JOG_MAX  
          else:
            self._feedrateRun+=delta_val*FEED_RUN_STEPS[0]
            if self._feedrateRun<C_FEED_RUN_MIN:
                self._feedrateRun=C_FEED_RUN_MIN
            elif self._feedrateRun>C_FEED_RUN_MAX:
                self._feedrateRun=C_FEED_RUN_MAX  
                   
          self.initRotaryStart()
          self.showFeed()






    def upd_rotary_on_drive(self,rotN:int):
        if self.rotaryObj[rotN]['value'] is None or self.rotaryObj[rotN]['rotary_on_mpos'] is None:
           return            
        delta_val = self.rotaryObj[rotN]['value'] - self.rotaryObj[rotN]['rotary_on_mpos']
        if delta_val==0 :
            return
        step = delta_val * self.rotaryObj[rotN]['unit'] *  self.rotaryObj[rotN]['scale']

        if self.rotaryObj[rotN]['axe']=='x':
            #self.grblJog(x=step, feedrate=self._feedrateRun)
            print('new pos ',self.rotaryObj[rotN]['axe'],step)
        elif self.rotaryObj[rotN]['axe']=='y':
            print('new pos ',self.rotaryObj[rotN]['axe'],step)
        elif self.rotaryObj[rotN]['axe']=='z':
            print('new pos ',self.rotaryObj[rotN]['axe'],step)




    def upd_rotary_on_feedJog(self,rotN:int):
        if self.rotaryObj[rotN]['value'] is None or self.rotaryObj[rotN]['rotary_on_mpos'] is None:
           return            
        delta_val = self.rotaryObj[rotN]['value'] - self.rotaryObj[rotN]['rotary_on_mpos']
        if delta_val==0 :
           return
        self._feedrateJog+=delta_val*FEED_JOG_STEPS[0]
        if self._feedrateJog<C_FEED_JOG_MIN:
            self._feedrateJog=C_FEED_JOG_MIN
        elif self._feedrateJog>C_FEED_JOG_MAX:
            self._feedrateJog=C_FEED_JOG_MAX  
        self.initRotaryStart()
        self.showFeed()

     


    def upd_rotary_on_feedRun(self,rotN:int):
        if self.rotaryObj[rotN]['value'] is None or self.rotaryObj[rotN]['rotary_on_mpos'] is None:
           return            
        delta_val = self.rotaryObj[rotN]['value'] - self.rotaryObj[rotN]['rotary_on_mpos']
        if delta_val==0 :
           return
        self._feedrateRun+=delta_val*FEED_RUN_STEPS[0]
        if self._feedrateJog<C_FEED_JOG_MIN:
            self._feedrateJog=C_FEED_JOG_MIN
        elif self._feedrateJog>C_FEED_JOG_MAX:
            self._feedrateJog=C_FEED_JOG_MAX  
        self.initRotaryStart()
        self.showFeed()            

    def upd_rotary_on_scaleXY(self,rotN:int):    
        if self.rotaryObj[rotN]['value'] is None or self.rotaryObj[rotN]['rotary_on_mpos'] is None:
           return        
        delta_val = self.rotaryObj[rotN]['value'] - self.rotaryObj[rotN]['rotary_on_mpos']
        if abs(delta_val)<2 :
           return
        
        try:
          index = DXYZ_STEPS.index(self._dXY)
        except ValueError:
          print(f"The value {self._dXY} is not in the array.")
          index = 0
        print(' _dXY index1',index)  
        index+=(1 if delta_val>0 else -1)
        print(' _dXY index2',index)  
        if index>=len(DXYZ_STEPS):
           self._dXY=DXYZ_STEPS[-1]
        elif index<0:
           self._dXY=DXYZ_STEPS[0]
        else:
           self._dXY=DXYZ_STEPS[index]

        self.initRotaryStart()
        self.showdXY()  
        
        

    def upd_rotary_on_scaleZ(self,rotN:int):
        if self.rotaryObj[rotN]['value'] is None or self.rotaryObj[rotN]['rotary_on_mpos'] is None:
           return            
        delta_val = self.rotaryObj[rotN]['value'] - self.rotaryObj[rotN]['rotary_on_mpos']
        if delta_val==0 :
           return
        
        try:
          index = DXYZ_STEPS.index(self._dZ)
        except ValueError:
          print(f"The value {self._dZ} is not in the array.")
          index = 0

        index+=(1 if delta_val>0 else -1)  
        if index>=len(DXYZ_STEPS):
           self._dZ=DXYZ_STEPS[-1]
        elif index<0:
           self._dZ=DXYZ_STEPS[0]
        else:
           self._dZ=DXYZ_STEPS[index]

        self.initRotaryStart()
        self.showdZ()          
        




    def showFeed(self) :     
        if self._ui_modes[self._ui_mode] in ('main','feedJog'):
          text='{:4.0f}'.format(self._feedrateJog)
        else:
          text='{:4.0f}'.format(self._feedrateRun)
        self.neoLabel(text,id='feed')

    def showdXY(self) : 
        if self._dXY<1.0:    
          self.neoLabel('{:4.2f}'.format(self._dXY),id='dXY')
        else:
           self.neoLabel('{:4.0f}'.format(self._dXY),id='dXY')
             
         
    def showdZ(self) :     
        if self._dZ<1.0: 
          self.neoLabel('{:4.2f}'.format(self._dZ),id='dZ')
        else:
          self.neoLabel('{:4.0f}'.format(self._dZ),id='dZ')

 


    def neoTerm(self,text,color=None) :   
        #print("neoTerm",text)  
        self.neoLabel(text,id='term',color=VFD_WHITE if color is None else  color)


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
        self.neoLabel(self.grblParams._grbl_info,id='term',color=VFD_WHITE )        
       
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
      if self._dXY*10.0>C_STEP_MAX:
           self._dXY =C_STEP_MAX
      else:   
           self._dXY *=10.0
      self.grblParams._state_prev='stepX'     
      #print('g_step+ now',self._dXY)         

    def dec_stepXY(self):
      if self._dXY*0.1<C_STEP_MIN:
           self._dXY =C_STEP_MIN
      else:   
           self._dXY *=0.1
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
      self._dXY=self.nextStepVals(self._dXY,DXYZ_STEPS)
      self.grblParams._state_prev='stepX'          
      #print('g_step _dXY now',self._dXY)     

    def stepZ(self):
      self._dZ=self.nextStepVals(self._dZ,DXYZ_STEPS)
      self.grblParams._state_prev='stepZ'          
      #print('g_step _dZ now',self._dZ)     

    def set_feedrate(self):
      self._feedrateJog=self.nextStepVals(self._feedrateJog, FEED_JOG_STEPS)
      self.grblParams._state_prev='feed'          
      #print('g_feedrate now',self._feedrate) 


    def inc_stepZ(self):
      if self._dXY*10.0>C_STEP_Z_MAX:
           self._dZ =C_STEP_Z_MAX
      else:   
           self._dZ *=10.0
      self.grblParams._state_prev='stepZ'          
      #print('g_step_z now',self._dZ)         

    def dec_stepZ(self):
      if self._dZ*0.1<C_STEP_Z_MIN:
           self._dZ =C_STEP_Z_MIN
      else:   
           self._dZ *=0.1
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
        #print ('upd_rotary: every 1s')
        for rotN in range(len(self.rotaryObj)):
            if self.rotaryObj[rotN]['obj'] is not None:
                #print ('upd_rotary: every 1s[2], rotN=',rotN, self._mPosInited , self.rotaryObj[rotN]['state'], self.rotaryObj[rotN]['value'])
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
                    #print ('upd_rotary: every 1s[2], rotN=',rotN, self._mPosInited , self.rotaryObj[rotN]['state'], self.rotaryObj[rotN]['value'],'mode',self._ui_modes[self._ui_mode])
                    if self._ui_modes[self._ui_mode] == 'main':
                      self.upd_rotary_on_main(rotN)
                    if self._ui_modes[self._ui_mode] == 'drive':
                      self.upd_rotary_on_drive(rotN)
                    if self._ui_modes[self._ui_mode] == 'feedJog':
                      self.upd_rotary_on_feedJog(rotN)
                    if self._ui_modes[self._ui_mode] == 'feedRun':
                      self.upd_rotary_on_feedRun(rotN)
                     



# G10L20P1Y0 bCNC set wpos g54(p1) for y = 0    https://linuxcnc.org/docs/html/gcode/g-code.html#gcode:g10-l2 
# G10 L20 is similar to G10 L2 except that instead of setting the offset/entry to the given value, it is set to a calculated value that makes the current coordinates become the given value.                   
#<Idle|MPos:14.000,31.000,8.000,0.000|Bf:100,1023|FS:0,0|Pn:P|WCO:0.000,31.000,6.000,0.000>
#MPos:14.000,31.000,8.000
#  minus
#  WCO:0.000,31.000,6.000
#WPOS:14.000,0.000,2.000