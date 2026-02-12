# display.py
# MicroPython driver for SSD1306 OLED display (TKJHAT)
#
# Based on the original TKJHAT Pico C SDK implementation
# Uses the standard MicroPython SSD1306 + FrameBuffer driver
#
# Features:
# - Text output (fixed position and XY)
# - Pixel drawing
# - Lines, rectangles, circles
# - Clear and power control
# - Simple, student-friendly API
#
# Behavior:
# - Functions automatically update the display (like original C version)
# - draw_pixel() does NOT auto-update (helper function)
# - I2C locking is handled inside show()


import time
import ssd1306


class Display:

    # Default display configuration (TKJHAT)

    WIDTH = 128
    HEIGHT = 64
    ADDRESS = 0x3C

    # Constructor

    def __init__(self, bus,
                 width: int = WIDTH,
                 height: int = HEIGHT,
                 address: int = ADDRESS):

        self.bus = bus
        self.width = width
        self.height = height
        self.address = address

     
        self.oled = ssd1306.SSD1306_I2C(
            width, height, bus.i2c, addr=address
        )


    # Initialization and power control


    def init(self):
        """
        Initialize and clear the display.
        """
        try:
            self.power_on()
            self.clear()
        except OSError:
            pass

    def power_on(self):
        """
        Turn the display on.
        """
        self.oled.poweron()

    def power_off(self):
        """
        Turn the display off.
        """
        self.oled.poweroff()


    # Internal update helper


    def show(self):
        """
        Update the physical display from the buffer.
        Locking prevents concurrent I2C access.
        """
        self.bus._acquire()
        try:
            self.oled.show()
        except OSError:
            print("Display I2C error")
            pass
        finally:
            self.bus._release()

 

    def clear(self):
        """
        Clear the display and update the screen.
        """
        self.oled.fill(0)
        self.show()

   
    # Text output 
  

    def write_text_xy(self, x: int, y: int, text: str, delay_ms: int = 0):
        """
        Write text at a specific (x, y) position.

        Coordinates outside the display are clipped.
        Automatically updates the display.
        """
        if not text:
            return

        x = max(0, x)
        y = max(0, y)

        self.oled.text(text, x, y)
        self.show()

        if delay_ms > 0:
            time.sleep_ms(delay_ms)

    def write_text(self, text: str, delay_ms: int = 0):
        """
        Write text at a default centered position.
        Automatically updates the display.
        """
        if not text:
            return

        self.oled.fill(0)
        self.oled.text(text, 8, 24)
        self.show()

        if delay_ms > 0:
            time.sleep_ms(delay_ms)


    # Drawing 
  

    def draw_pixel(self, x: int, y: int):
        """
        Draw a single pixel with bounds checking.
        Does NOT auto-update (helper function).
        """
        if 0 <= x < self.width and 0 <= y < self.height:
            self.oled.pixel(x, y, 1)

    def draw_line(self, x0: int, y0: int, x1: int, y1: int):
        """
        Draw a line between two points and update display.
        """
        self.oled.line(x0, y0, x1, y1)
        self.show()

    def draw_rectangle(self, x: int, y: int, w: int, h: int, fill: bool = False):
        """
        Draw a rectangle (filled or outline) and update display.
        """
        if fill:
            self.oled.fill_rect(x, y, w, h, 1)
        else:
            self.oled.rect(x, y, w, h, 1)

        self.show()

    def draw_circle(self, x0: int, y0: int, r: int, fill: bool = False):
        """
        Draw a circle using a simple midpoint algorithm and update display.
        """
        if r <= 0:
            return

        x = r
        y = 0
        err = 0

        while x >= y:
            points = [
                (x0 + x, y0 + y), (x0 + y, y0 + x),
                (x0 - y, y0 + x), (x0 - x, y0 + y),
                (x0 - x, y0 - y), (x0 - y, y0 - x),
                (x0 + y, y0 - x), (x0 + x, y0 - y)
            ]

            for px, py in points:
                self.draw_pixel(px, py)

            if fill:
                self.oled.hline(x0 - x, y0 + y, 2 * x, 1)
                self.oled.hline(x0 - x, y0 - y, 2 * x, 1)

            y += 1
            err += 1 + 2 * y
            if 2 * (err - x) + 1 > 0:
                x -= 1
                err += 1 - 2 * x

        self.show()