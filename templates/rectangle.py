from turtle import left


class App():
    __version__ = '0.1'
    width:float = 10.0
    height:float = 5.0
    feed:float = 100.0
    zfeed:float = 10.0
    toolDiameter:float = 8.0
    down:float =1.0
    dz:float = 0.1
    
    def __init__(self):
        #self.diameter = 20
        #self.feed = 200
        pass
        
        
    def getGcode(self):
        cmd='G21 G17 G90 ' # Set units to millimeters, select XY plane, use absolute positioning'
        cmd+=f'\nG0 X0 Y0 F{self.feed}' # Rapid move to the start position (0,0) with a feed rate of 500mm/min
        cmd+=f'\nM3 S1000' # Turn on the spindle (or laser), adjust speed (S value) as needed
        cmdOne =f'G01 X{self.width} Y0\nG01 X{self.width} Y{self.height}\nG01 X0 Y{self.height}\nG01 X0 Y0'
        cmd+=f'\n{cmdOne}'
        while self.down >= 0:
            cmd+=f'\nG1 Z-{self.dz} F{self.zfeed}' # Plunge the tool to a depth of -1mm
            self.down -= self.dz
            cmd+=f'\n{cmdOne}'
        cmd+='\nG0 Z5' # Lift the tool clear
        cmd+='G0 X0 Y0' # Return to origin
        return cmd
    
    def getIcon(self):
        return [{"name": "rectangle", "shape": "rect", "width": self.width, "height": self.height, "fill": True, "color": "red"}]
