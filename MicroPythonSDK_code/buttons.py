# buttons.py
# MicroPython driver for TKJHAT buttons
#
# Based on the TKJHAT Pico C SDK implementation
#
# Features:
# - Two active-high buttons
# - Simple polling interface
# - Intended for user input and control


from machine import Pin


class Buttons:

    # Button pins (TKJHAT)

    BUTTON1_PIN = 2
    BUTTON2_PIN = 22


    # Constructor

    def __init__(self,
                 button1_pin: int = BUTTON1_PIN,
                 button2_pin: int = BUTTON2_PIN):
        self.button1_pin = button1_pin
        self.button2_pin = button2_pin

        self.button1 = None
        self.button2 = None


    # Initialization

    def init(self):
        """
        Initialize both buttons as input pins.

        Buttons are active-high.
        Internal pull-down resistors are enabled for stable readings.
        """
        self.button1 = Pin(self.button1_pin, Pin.IN, Pin.PULL_DOWN)
        self.button2 = Pin(self.button2_pin, Pin.IN, Pin.PULL_DOWN)


    # Read button state

    def button1_pressed(self) -> bool:
        """
        Return True if button 1 is pressed.
        """
        return self.button1.value() == 1


    def button2_pressed(self) -> bool:
        """
        Return True if button 2 is pressed.
        """
        return self.button2.value() == 1


    def any_pressed(self) -> bool:
        """
        Return True if either button is pressed.
        """
        return self.button1_pressed() or self.button2_pressed()
