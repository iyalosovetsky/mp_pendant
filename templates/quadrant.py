
class App():
    __version__ = '0.1'
    
    __slots__ = ['diameter','feed','zfeed','toolDiameter','down','dz','width','height']
    
    def __init__(self):
        self.diameter:float = 10.0
        self.feed:float = 100.0
        self.zfeed:float = 10.0
        self.toolDiameter:float = 8.0
        self.down:float =1.0
        self.dz:float = 0.1
        self.width:float = 10.0
        self.height:float = 10.0
        
        
    def getGcode(self):
        cmd=';quadrant: diameter,feed,zfeed,toolDiameter,down,dz' # Set units to millimeters, select XY plane, use absolute positioning'
        cmd+='\nG21 G17 G90 ' # Set units to millimeters, select XY plane, use absolute positioning'
        cmd+=f'\nG0 X0 Y0 F{self.feed}' # Rapid move to the start position (0,0) with a feed rate of 500mm/min
        cmd+=f'\nM3 S1000' # Turn on the spindle (or laser), adjust speed (S value) as needed
        cmdOne =f'\nG01 X{self.width} Y0\nG01 X{self.width} Y{self.width}\nG01 X0 Y{self.width}\nG01 X0 Y0'
        cmd+=f'\n{cmdOne}'
        while self.down >= 0:
            cmd+=f'\nG1 Z-{self.dz} F{self.zfeed}' # Plunge the tool to a depth of -1mm
            self.down -= self.dz
            cmd+=f'\n{cmdOne}'
        cmd+='\nG0 Z5' # Lift the tool clear
        cmd+='G0 X0 Y0' # Return to origin
        return cmd
    
    def getIcon(self):
        return [{"name": "quadrant", "shape": "rect", "width": self.width, "height": self.width, "fill": True, "color": "red"}]
