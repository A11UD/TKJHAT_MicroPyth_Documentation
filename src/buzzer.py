# buzzer.py
# MicroPython driver for the TKJHAT buzzer
#
# Based on the TKJHAT Pico C SDK implementation
#
# Features:
# - Simple tone generation using PWM
# - Blocking play function
# - Intended for alerts and feedback sounds


import time
from machine import Pin, PWM


class Buzzer:

    # Buzzer pin (TKJHAT)

    BUZZER_PIN = 17


    # Constructor

    def __init__(self, pin: int = BUZZER_PIN):
        self.pin = pin
        self.pwm = None


    # Low-level helpers

    def _ensure_pwm(self):
        """
        Initialize PWM if not already initialized
        """
        if self.pwm is None:
            self.pwm = PWM(Pin(self.pin))
            self.pwm.duty_u16(0)


    # Public API (student-facing)

    def init(self):
        """
        Initialize the buzzer
        """
        self._ensure_pwm()
        self.turn_off()


    def play_tone(self, frequency_hz: int, duration_ms: int):
        """
        Play a tone on the buzzer.

        This function is blocking for the duration of the tone.

        :param frequency_hz: Tone frequency in Hz
        :param duration_ms: Duration in milliseconds
        """
        if frequency_hz <= 0 or duration_ms <= 0:
            return

        self._ensure_pwm()

        self.pwm.freq(int(frequency_hz))
        self.pwm.duty_u16(32768)   # 50 % duty cycle

        time.sleep_ms(int(duration_ms))

        self.turn_off()


    def turn_off(self):
        """
        Turn the buzzer off
        """
        if self.pwm is not None:
            self.pwm.duty_u16(0)


    def deinit(self):
        """
        Deinitialize the buzzer and release the pin
        """
        if self.pwm is not None:
            self.pwm.deinit()
            self.pwm = None
