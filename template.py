
import gc

loaded_app= None
class Template:
    """
    A class to hold grbl parameters.
    Using __slots__ for memory optimization.
    """
    #__slots__ = ['diameter','feed','zfeed','toolDiameter','down','dz','width','height','app']

    def __init__(self, template_name:str, template_dir:str='/templates',
                 diameter:float = None, feed:float = None, zfeed:float = None, 
                 toolDiameter:float = None, down:float =None, dz:float = None,
                 width:float = None, height:float = None):
        # self.width:float = width
        # self.height:float = height
        # self.feed:float = feed
        # self.zfeed:float = zfeed
        # self.toolDiameter:float = toolDiameter
        # self.diameter:float = diameter
        # self.down:float = down  
        # self.dz:float = dz
        global loaded_app
        loaded_app=None
        self.app=None
        self.template_name=template_name.replace('.py','')
        self.template_dir=template_dir
        self.params={}
        self.loadApp()
        #self.setParams(feed=feed, zfeed=zfeed, toolDiameter=toolDiameter, down=down, dz=dz)
        self.setParams()
        
    
    def loadApp(self ):
        global loaded_app
        try:
            loaded_app = None
            gc.collect()
            module_name = f'{self.template_dir}.{self.template_name.lower()}'
            module = __import__(module_name, globals(), locals(), ['App'])
            global loaded_app 
            loaded_app = module.App()
            self.app=loaded_app

        except Exception as e:
            print(f"Error loading app for macro '{self.template_name}': {e}")
            self.app = None
    
    def setParams(self, **kwargs):
        if loaded_app is None:
            return
        for key in loaded_app.__slots__:
            #print('key=',key)
            if key.startswith('__'):
                continue
            if key in kwargs:
                #print(f"{key} in defaults and  equals " , kwargs.get(key))
                self.params[key]=kwargs.get(key)
            elif hasattr(loaded_app, key): 
                #print(f"{key} found in app ")
                vv=None
                #vv=eval('loaded_app.'+key)
                
                try:
                    vv=eval('loaded_app.'+key)  
                except AttributeError:
                    print('Attribute not found', key)  
                except NameError :    
                    print('Name error not found', 'loaded_app.'+key)  
                #print(f"{key} equal ={vv} ")    
                if vv is not None:
                    #print(f"{key} found in app and added to params with  ",vv)
                    self.params[key]=vv    
            else: 
                print('Warning Attribute not found in template but declared', key)  

        #print('Template.setParams: found params',self.params)            
             

    def updateParams(self):
        print('updateParams: need param update',loaded_app,self.params, 'app=None' if loaded_app is None else 'app!=None')
        if loaded_app is None:
            return
        loaded_app.setParams(self.params)


    def getGcode(self):
        if self.app is None:
            return None
        return self.app.getGcode()

    def getIcon(self):
        if self.app is None:
            return None
        return self.app.getIcon()            