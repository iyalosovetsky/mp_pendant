
import gc

class Template:
    """
    A class to hold grbl parameters.
    Using __slots__ for memory optimization.
    """
    #__slots__ = ['diameter','feed','zfeed','toolDiameter','down','dz','width','height','app']

    def __init__(self, template_name:str, template_dir:str='/templates',
                 diameter:float = 10.0, feed:float = 100.0, zfeed:float = 10.0, 
                 toolDiameter:float = 8.0, down:float =1.0, dz:float = 0.1,
                 width:float = 10.0, height:float = 20.0):
        self.width:float = width
        self.height:float = height
        self.feed:float = feed
        self.zfeed:float = zfeed
        self.toolDiameter:float = toolDiameter
        self.diameter:float = diameter
        self.down:float = down  
        self.dz:float = dz
        self.app=None
        self.template_name=template_name.replace('.py','')
        self.template_dir=template_dir
        self.params={}
        self.loadApp()
        self.setParams(feed=feed, zfeed=zfeed, toolDiameter=toolDiameter, down=down, dz=dz)
        
    
    def loadApp(self ):
        try:
            self.app = None
            gc.collect()
            module_name = f'{self.template_dir}.{self.template_name.lower()}'
            module = __import__(module_name, globals(), locals(), ['App'])
            self.app = module.App()

        except Exception as e:
            print(f"Error loading app for macro '{self.template_name}': {e}")
            self.app = None
    
    def setParams(self, **kwargs):
        if self.app is None:
            return
        for key in self.app.__slots__:
            print('key=',key)
            if key.startswith('__'):
                continue
            if key in kwargs:
                print(f"{key} in defaults and  equals " , kwargs.get(key))
                self.params[key]=kwargs.get(key)
            elif hasattr(self.app, key): 
                print(f"{key} found in app ")
                vv=None
                vv=eval('self.app.'+key)
                try:
                    vv=eval('self.app.'+key)  
                except AttributeError:
                    print('Attribute not found', key)  
                except NameError :    
                    print('Name error not found', 'self.app.'+key)  
                if vv is not None:
                    print(f"{key} found in app and added to params with  ",vv)
                    self.params[key]=vv    
            else: 
                print('Warning Attribute not found in template but declared', key)  

        print('found params',self.params)            
             

    def getGcode(self):
        if self.app is None:
            return None
        return self.app.getGcode()

    def getIcon(self):
        if self.app is None:
            return None
        return self.app.getIcon()            