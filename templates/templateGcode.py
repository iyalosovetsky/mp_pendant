class TemplateGcode():
    __version__ = '0.1'
    #__slots__ = ['diameter','feed','zfeed','toolDiameter','down','dz','__z']
    __slots__ = ['feed','zfeed','toolDiameter','down','dz','__z']
    
    
    def __init__(self):
        #self.diameter:float = 10.0
        self.feed:float = 100.0
        self.zfeed:float = 10.0
        self.toolDiameter:float = 8.0
        self.down:float =1.0
        self.dz:float = 0.1
        self.__z:float = 0.0
        
        

    
    
    def getInitGcode(self):
        cmd=[]
        cmd.append(';'+self.__shape__+': '+(','.join([nn  for nn in self.__slots__ if not nn.startswith('__')]))) # Set units to millimeters, select XY plane, use absolute positioning'
        cmd.append('G21 G17 G90') # Set units to millimeters, select XY plane, use g91 relative positioning'
        cmd.append('G10L20P1X0Y0Z0') # Set g54 to 0,0,0
        #cmd.append(f'G0 X0 Y0 F{self.feed}') # Rapid move to the start position (0,0) with a feed rate of 500mm/min
        cmd.append('M3') # Turn on the spindle (or laser), adjust speed (S value) as needed
        return cmd
    
    def getDzGcode(self):
        return ['G1 Z{z} F{zfeed}'] # Plunge the tool to a depth of -1mm


    def getEndGcode(self):
        cmd=[]
        cmd.append('M5') # Lift the tool clear
        cmd.append('G0 Z5') # Lift the tool clear
        cmd.append(f'G0 X0 Y0 F{self.feed}') # Return to origin

        return cmd

    def getGcode(self):
        cmd=self.getInitGcode()
        cmdOne = self.getOneLayerGcode()
        cmdDown = self.getDzGcode()
        cmd.extend(cmdOne)
        pos = self.down
        while pos >= 0:
            pos -= self.dz
            self.__z = pos-self.down
            
            cmd.extend([ll.format(z=self.__z,zfeed=self.zfeed) for ll in cmdDown])
            cmd.extend(cmdOne)
        cmd.extend(self.getEndGcode())    
        return cmd