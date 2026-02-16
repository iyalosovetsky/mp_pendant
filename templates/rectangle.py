from templates.templateGcode import TemplateGcode

class App(TemplateGcode):
    __version__ = '0.1'
    __slots__ = ['width','height','feed','zfeed','toolDiameter','down','dz','__shape__']
    
    
    def __init__(self):
        self.width:float = 10.0
        self.height:float = 20.0
        self.feed:float = 100.0
        self.zfeed:float = 10.0
        self.toolDiameter:float = 8.0
        self.down:float =1.0
        self.dz:float = 0.1
        self.__shape__  = 'rectangle'
    
    def getIcon(self):
        return [{"name": self.__shape__, "shape": "rect", "width": self.width, "height": self.height, "fill": True, "color": "red"}]
    
    

    def getOneLayerGcode(self):
        return f'G1 X{self.width} Y0 F{self.feed} \nG1 X{self.width} Y{self.height}\nG1 X0 Y{self.height}\nG1 X0 Y0'.splitlines()

