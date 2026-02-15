class App():
    __version__ = '0.1'
    diameter:float = 10.0
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
        cmd+=f'\nG02 X0 Y0 I{self.diameter/2} J0' # Clockwise arc back to the start point (X0 Y0) with I offset 10 (center is at X10)
        while self.down >= 0:
            cmd+=f'\nG1 Z-{self.dz} F{self.zfeed}' # Plunge the tool to a depth of -1mm
            self.down -= self.dz
            cmd+=f'\nG02 X0 Y0 I{self.diameter/2} J0' # Clockwise arc back to the start point (X0 Y0) with I offset 10 (center is at X10)
        cmd+='\nG0 Z5' # Lift the tool clear
        cmd+='G0 X0 Y0' # Return to origin
        return cmd
    
    def getIcon(self):
        return [{"name": "circle", "shape": "ellipse", "width": self.diameter/2, "height": self.diameter/2, "fill": True, "color": "blue"}]
