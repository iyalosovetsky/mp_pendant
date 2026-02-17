from templates.templateGcode import TemplateGcode

class App(TemplateGcode):
    __version__ = '0.1'
    __slots__ = ['diameter','feed','zfeed','toolDiameter','down','dz','__shape__','__z']
    
    diameter:float = 10.0
    feed:float = 100.0
    zfeed:float = 10.0
    toolDiameter:float = 8.0
    down:float =1.0
    dz:float = 0.1
    __shape__  = 'circle'
    __z:float = 0.0
    
    def __init__(self):
        pass
        
        
  
    
    def getIcon(self):
        return [{"name": self.__shape__, "shape": "ellipse", "width": self.diameter/2, "height": self.diameter/2, "fill": True, "color": "blue"}]
    

    def getOneLayerGcode(self):
        return f'G02 X0 Y0 I{self.diameter/2} J0 F{self.feed}'.splitlines() # Clockwise arc back to the start point (X0 Y0) with I offset 10 (center is at X10)

