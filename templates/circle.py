from templates.templateGcode import TemplateGcode

class App(TemplateGcode):
    __version__ = '0.1'
    __slots__ = ['diameter','feed','zfeed','toolDiameter','down','dz','__shape__','__z']
    
    
    def __init__(self):
        self.diameter:float = 10.0
        self.feed:float = 100.0
        self.zfeed:float = 10.0
        self.toolDiameter:float = 8.0
        self.down:float =1.0
        self.dz:float = 0.1
        self.__shape__  = 'circle'
        self.__z:float = 0.0
        
  
    
    def getIcon(self):
        return [{"name": self.__shape__, "shape": "ellipse", "width": self.diameter/2, "height": self.diameter/2, "fill": True, "color": "blue"}]
    

    def getOneLayerGcode(self):
        return f'G02 X0 Y0 I{self.diameter/2} J0 F{self.feed}'.splitlines() # Clockwise arc back to the start point (X0 Y0) with I offset 10 (center is at X10)

