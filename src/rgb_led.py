from machine import Pin, PWM

class Rgb_led:

    # Pin Addresses
    RGB_LED_R = 18
    RGB_LED_G = 19
    RGB_LED_B = 20
    # PWM frequency
    RGB_FREQ = 480

    # Constructor
    def __init__(self):
        self.pwm_r = None
        self.pwm_g = None
        self.pwm_b = None
        self.initialized = False


    # Public API

    def init(self):
        """Initialize rgb pins to use PWM"""
        self.pwm_r = PWM(Pin(self.RGB_LED_R), freq=self.RGB_FREQ)
        self.pwm_g = PWM(Pin(self.RGB_LED_G), freq=self.RGB_FREQ)
        self.pwm_b = PWM(Pin(self.RGB_LED_B), freq=self.RGB_FREQ)
        self.initialized = True


    def write(self, r: int, g: int, b: int):
        """
        Set color for rgb led using values in range 0-255 (0 = off, 255 = full on)
        
        :param r: red intensity (0-255, 0 = off, 255 = full on)
        :type r: int
        :param g: green intensity (0-255, 0 = off, 255 = full on)
        :type g: int
        :param b: blue intensity (0-255, 0 = off, 255 = full on)
        :type b: int
        """
        if self.initialized:
            #ensure values are in range 0-255
            r = 0 if r < 0 else 255 if r > 255 else r
            g = 0 if g < 0 else 255 if g > 255 else g
            b = 0 if b < 0 else 255 if b > 255 else b

            #Invert the values
            r = 255 - r
            g = 255 - g
            b = 255 - b

            #Convert the 0-255 values to a 16-bit duty cycle (0-65535) (linearly)
            r_value = r * r
            g_value = g * g
            b_value = b * b

            #Set the rgb values
            self.pwm_r.duty_u16(r_value)
            self.pwm_g.duty_u16(g_value)
            self.pwm_b.duty_u16(b_value)



    def stop(self):
        """Disable the PWM output for rgb pins"""

        if self.initialized:

            # Set output to 0
            self.write(0, 0, 0)

            # Disable the PWM output
            self.pwm_r.deinit()
            self.pwm_g.deinit()
            self.pwm_b.deinit()

            # Set pins to Hi‑Z/off state
            Pin(self.RGB_LED_R, Pin.IN)
            Pin(self.RGB_LED_G, Pin.IN)
            Pin(self.RGB_LED_B, Pin.IN)

            self.initialized = False
            
