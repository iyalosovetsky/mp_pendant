import time

from micropython import const
from machine import Pin



class Button:

    def __init__(self, pin, callback=None,callback_long=None, debounce_time=200, long_press_time=1000):
        self.button = pin
        self.callback = callback
        self.callback_long = callback_long
        self.debounce_time = debounce_time
        self.long_press_time = long_press_time # мс (1 секунда)
        self.last_press_time = 0
        self.button_pressed = False
        self.button.irq(trigger=Pin.IRQ_FALLING | Pin.IRQ_RISING, handler=self.button_handler)


    def button_handler(self,pin):
        current_time = time.ticks_ms()
        
        # Дебаунсинг: перевірка часу з останнього натискання
        if time.ticks_diff(current_time, self.last_press_time) > self.debounce_time:
            if pin.value() == 0: # Кнопка натиснута
                self.button_pressed = True
                self.last_press_time = current_time
            else: # Кнопка відпущена
                if self.button_pressed:
                    press_duration = time.ticks_diff(current_time, self.last_press_time)
                    if press_duration > self.long_press_time:
                        # print("Довге натискання")
                        if self.callback_long is not None:
                            self.callback_long(pin,self)
                    else:
                        # print("Коротке натискання")
                        if self.callback is not None:
                            self.callback(pin,self)
                    self.button_pressed = False



 

 