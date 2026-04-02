from templates.templateGcode import TemplateGcode

class App(TemplateGcode):
    __version__ = '0.1'
    __slots__ = ['width','height','feed','zfeed','toolDiameter','down','back','dz','__shape__','__z']
    
    
    def __init__(self):
        self.width:float = 20.0
        self.height:float = 35.0
        self.feed:float = 250.0
        self.zfeed:float = 10.0
        self.toolDiameter:float = 6.0
        self.down:float =15.0
        self.dz:float = 0.3
        self.back:float = 1.0
        self.__shape__  = 'rectTBF'
        self.__z:float = 0.0
    

    def getIcon(self):
        y0=int(self.height) if self.back>=0.99 else 0
        return [{"name": self.__shape__, "shape": "rect", "width": self.width, "height": self.height, "x": 0, "y": 0, "fill": True, "color": "yellow"},
                {"name": "origin", "shape": "origin", "x": 0, "y":  y0 , "width": 3, "height": 3, "fill": True, "color": "blue"},
                {"name": "arrow", "shape": "arrow", "x": 0, "y":  y0 , "width": self.width*3//4, "height": (self.height*(1 if self.back>=0.99 else -1 ))//8, "fill": True, "color": "red"}
                ]
    
    def  getOriginGcode(self,loop=1):
        delta=self.toolDiameter*loop/2
        if self.back>=0.99:
            x0=delta
            y0=-delta
        else:
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
            if self.back>=0.99:
                gcode.extend(f'G91 G1 X{w} Y0 \nG1 X0 Y-{h}\nG1 X-{w} Y0\nG1 X0 Y{h}'.splitlines())
            else:
                gcode.extend(f'G91 G1 X{w} Y0 \nG1 X0 Y{h}\nG1 X-{w} Y0\nG1 X0 Y-{h}'.splitlines())    
            gcode.append('G91')
            if w<self.width/2 and h<self.height/2:
                break



        return gcode

                    