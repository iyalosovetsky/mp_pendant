from templates.templateGcode import TemplateGcode

class App(TemplateGcode):
    __version__ = '0.1'
    __slots__ = ['width','height','feed','zfeed','toolDiameter','down','dz','__shape__','__z']
    
    
    def __init__(self):
        self.width:float = 35.0
        self.height:float = 21.0
        self.feed:float = 100.0
        self.zfeed:float = 10.0
        self.toolDiameter:float = 8.0
        self.down:float =1.0
        self.dz:float = 0.1
        self.__shape__  = 'rectTF'
        self.__z:float = 0.0
    
    def getIcon(self):
        return [{"name": self.__shape__, "shape": "rect", "width": self.width, "height": self.height, "fill": True, "color": "yellow"},
                {"name": "origin", "shape": "origin", "x": 0, "y": 0, "width": 3, "height": 3, "fill": True, "color": "blue"}]
    
    def  getOriginGcode(self,loop=1):
        delta=self.toolDiameter*loop/2
        x0=delta
        y0=delta
        return f'G90 G1 X{x0} Y{y0} F{self.feed}'.splitlines() # absolute


    def getOneLayerGcode(self):
        
        gcode=[]
        ii=0
        
        while ii<2000:
            ii+=1
            delta=self.toolDiameter/2*ii
            w=self.width-2*delta
            h=self.height-2*delta
            if w<0: w=0
            if h<0: h=0
            if w<=0 and h<=0:
                break

            gcode.extend(self.getOriginGcode(ii))
            # gcode.extend(f'G91 G1 X{w} Y0 \nG1 X{w} Y{h}\nG1 X0 Y{h}\nG1 X0 Y0'.splitlines())
            gcode.extend(f'G91 G1 X{w} Y0 \nG1 X0 Y{h}\nG1 X-{w} Y0\nG1 X0 Y-{h}'.splitlines())
            gcode.append('G91')



        return gcode

                    