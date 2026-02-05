'''
Module containing functions for controlling TKJHAT leds
'''
from machine import Pin
from utime import sleep

class Led:

    # GPIO Address
    RED_LED_PIN = 14
    TOGGLE_SLEEP_TIME = 120

    # Constructor
    def __init__(self):
        self.pin = None

    def init(self):
        """Initialize red led"""
        self.pin = Pin(self.RED_LED_PIN, Pin.OUT)

    def toggle(self):
        """Toggle red led"""
        if self.pin is not None:
            self.pin.toggle()
    
    def set_status(self, status):
        """Set status for red led (boolean). False = off, True = on"""
        if self.pin is not None:
            self.pin.value(status)

    def blink(self, n: int):
        """Blink red led n times"""
        if self.pin is not None:
            for i in range(n):
                self.pin.toggle()
                sleep(self.TOGGLE_SLEEP_TIME)
                self.pin.toggle()
                sleep(self.TOGGLE_SLEEP_TIME)
            self.pin.value(False)
            