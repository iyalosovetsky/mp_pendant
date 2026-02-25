import time

from micropython import const
from machine import Pin



class Button:

    def __init__(self, pin, callback=None,callback_long=None, debounce_time=100, long_press_time=500, pin2=None, callback2=None,callback2_long=None): 
        self.button = pin
        self.pin2 =pin2
        self.callback = callback
        self.callback_long = callback_long
        self.callback2 = callback2
        self.callback2_long = callback2_long
        self.debounce_time = debounce_time
        self.long_press_time = long_press_time # мс (1 секунда)
        self.last_press_time = 0
        self.button_pressed = False
        self.prev_val = 1
        self.val = 1
        self.val2 = 1
        if pin2 is not None and (self.callback2_long is not None or self.callback2 is not None):
             self.val2 = self.pin2.value()
             self.button.irq(trigger=Pin.IRQ_FALLING|Pin.IRQ_RISING, handler=self.button_handler2)
        else:     
            self.button.irq(trigger=Pin.IRQ_FALLING|Pin.IRQ_RISING, handler=self.button_handler)


    def button_handler(self,pin):
        self.prev_val=self.val
        self.val=pin.value()
        current_time = time.ticks_ms()
        if self.val == self.prev_val:
            if time.ticks_diff(current_time, self.last_press_time) > self.long_press_time:
                self.last_press_time=current_time
            #print('in handler point2/0 the same',self.val)
            return
        if time.ticks_diff(current_time, self.last_press_time) < self.debounce_time:
            #print('in handler point2/1 timeout',self.val)
            return
        
        #print('in handler point2',self.val)
        if self.val == 0: # Кнопка натиснута
            self.last_press_time = current_time
        else: # Кнопка відпущена
                press_duration = time.ticks_diff(current_time, self.last_press_time)
                if press_duration > self.long_press_time:
                    # print("Довге натискання")
                    if self.callback_long is not None:
                        self.callback_long(pin,self)
                else:
                    # print("Коротке натискання")
                    if self.callback is not None:
                        self.callback(pin,self)
                    

    def button_handler00(self,pin):
        self.val=pin.value()
        current_time = time.ticks_ms()
        if self.val == 0: # Кнопка натиснута
            self.last_press_time = current_time
        else: 
            if self.last_press_time>0 and time.ticks_diff(current_time, self.last_press_time)> self.long_press_time:
                self.last_press_time = 0
                if self.callback_long is not None:
                        self.callback_long(pin,self)
            elif self.last_press_time>0 and time.ticks_diff(current_time, self.last_press_time)> self.debounce_time:
                self.last_press_time = 0
                if self.callback is not None:
                        self.callback(pin,self)
            self.last_press_time = 0 

    def button_handler2(self,pin):
        self.val=pin.value()
        self.val2=self.pin2.value()
        current_time = time.ticks_ms()
        if self.val == 0: # Кнопка натиснута
            self.last_press_time = current_time
        else: 
            if self.last_press_time>0 and time.ticks_diff(current_time, self.last_press_time)> self.long_press_time:
                self.last_press_time = 0
                if self.val2==0 and  self.callback2_long is not None:
                   self.callback2_long(pin,self)
                   return
                if self.callback_long is not None:
                        self.callback_long(pin,self)
            elif self.last_press_time>0 and time.ticks_diff(current_time, self.last_press_time)> self.debounce_time:
                self.last_press_time = 0
                if self.val2==0 and  self.callback2 is not None:
                   self.callback2(pin,self)
                   return
                if self.callback is not None:
                   self.callback(pin,self)
            self.last_press_time = 0             

 

 