class TemplateGcode():
    __version__ = '0.1'
    __slots__ = ['diameter','feed','zfeed','toolDiameter','down','dz']
    
    
    def __init__(self):
        self.diameter:float = 10.0
        self.feed:float = 100.0
        self.zfeed:float = 10.0
        self.toolDiameter:float = 8.0
        self.down:float =1.0
        self.dz:float = 0.1
        
        

    
    
    def getInitGcode(self):
        cmd=[]
        cmd.append(';'+self.__shape__+': '+(','.join([nn  for nn in self.__slots__ if not nn.startswith('__')]))) # Set units to millimeters, select XY plane, use absolute positioning'
        cmd.append('G21 G17 G91') # Set units to millimeters, select XY plane, use g91 relative positioning'
        cmd.append(f'G0 X0 Y0 F{self.feed}') # Rapid move to the start position (0,0) with a feed rate of 500mm/min
        cmd.append('M3') # Turn on the spindle (or laser), adjust speed (S value) as needed
        return cmd
    
    def getDzGcode(self):
        return f'G1 Z-{self.dz} F{self.zfeed}'.splitlines() # Plunge the tool to a depth of -1mm


    def getEndGcode(self):
        cmd=[]
        cmd.append('M5') # Lift the tool clear
        cmd.append('G0 Z5') # Lift the tool clear
        cmd.append('G0 X0 Y0') # Return to origin

        return cmd

    def getGcode(self):
        cmd=self.getInitGcode()
        cmdOne = self.getOneLayerGcode()
        cmdDown = self.getDzGcode()
        cmd.extend(cmdOne)
        while self.down >= 0:
            self.down -= self.dz
            cmd.extend(cmdDown)
            cmd.extend(cmdOne)
        cmd.extend(self.getEndGcode())    
        return cmd