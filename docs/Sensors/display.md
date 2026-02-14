# Display - SSD1306

### Detailed Description.
This module provides a MicroPython API for the SSD1306 128 x 64 OLED display used on the TKJHAT extension board.
The display is controlled over the I2C at address 0x3C.
This driver is based on the original TKJHAT Pico C SDK and uses the standard MicroPython ssd1306 + FrameBuffer driver.

#### Features
- Text Output (fixed and XY positioning)
- Pixel drawing
- Line, Rectangle and Circle drawing
- Automatic screen updating
- Internal I2C locking support with **I2CBusManager**

#### Behavior
- All drawing functions automatically update the display.
- draw_pixel() does not automatically update the display (helper function).
- I2C access is protected using lock inside show() when I2CBusManager is used.
- Designed to behave like the original C SDK version.

## Default Connections (TKJHAT)

| Signal              | MicroPython / Board              | GPIO | Description                               |
|---------------------|----------------------------------|------|-------------------------------------------|
| SDA                 | I2C(..., sda=Pin(12))            | 12   | I2C data                                  |
| SCL                 | I2C(..., scl=Pin(13))            | 13   | I2C clock                                 |
| Address             | 0x3C                             | –    | SSD1306 I2C address                       |
| Resolution          | 128 x 64                         |      | Display resolution                        |

### Usage example
**Precondition:** Precondition: The I2C interface must be initialized before using the display.

```python
from machine import I2C, Pin
from bus_manager import I2CBusManager
from display import Display
import time

# I2C Setup

i2c = I2C(0, sda=Pin(12), scl=Pin(13), freq=400_000)
bus = I2CBusManager(i2c)

display = Display(bus)
display.init()

# Text Output

display.write_text("TKJHAT")
time.sleep(1.5)

display.clear()
display.write_text_xy(0, 0, "SSD1306 Demo")
display.write_text_xy(0, 16, "Line")
display.write_text_xy(0, 32, "Rectangle")
display.write_text_xy(0, 48, "Circle")
time.sleep(2)

# Line Drawing

display.clear()
display.draw_line(0, 0, 127, 63)
time.sleep(1.5)

# Rectangle Drawing

display.clear()
display.draw_rectangle(10, 10, 50, 30, fill=False)
time.sleep(1.5)

display.clear()
display.draw_rectangle(10, 10, 50, 30, fill=True)
time.sleep(1.5)

# Circle Drawing

display.clear()
display.draw_circle(64, 32, 20, fill=False)
time.sleep(1.5)

display.clear()
display.draw_circle(64, 32, 20, fill=True)
time.sleep(1.5)

# Power Control

display.clear()
display.write_text("Power Off")
time.sleep(1)

display.power_off()
time.sleep(2)

display.power_on()
display.write_text("Power On")
time.sleep(2)

display.clear()
```

## Display code documentation
**class Display(bus)**
Create an SSD1306 display instance using:
- I2CBusManager

## Function Documentation

# `init()`
**What it does:**

- Powers on the display
- Clears the screen

#### Precondition:
- I2C bus must be initialized (SDA = 12, SCL = 13, freq = 400 kHz)
- Display must be connected at address 0x3C

#### Postcondition:
- Display is powered and cleared

# `power_on()`
- Turn the display on.

# `power_off()`
- Turn the display off.

# `clear()`
- Clear the display buffer and update the screen.
- Fills screen with black

# `show()`
- Update the physical display from the internal buffer.
#### Notes:
- Automatically called by drawing functions
- Handles I2C locking internally.

# `write_text_xy(x: int, y: int, text: str, delay_ms: int = 0)`
Write text at spesific (x, y) coordinates.

#### Parameters:
- **x**: Horizontal positioning (0 - 127)
- **y**: Vertical positioning (0 - 63)
- **text**: String to display.
- **delay_ms**: Optional delay after update.  


# `write_text(text: str, delay_ms: int = 0)`
Write text at centered position. (8, 24)

#### Parameters:
- **text**: String to display.
- **delay_ms**: Optional delay after update.  


# `draw_line(x0, y0, x1, y1)`
Draw a line between two points.

#### Parameters:
- **x0**, **y0**: Starting point.
- **x1**, **y1**: Ending point.

# `draw_rectangle(x, y, w, h, fill=False)`
Draw a rectangle.

#### Parameters:
- **x, y**: Top-left corner.
- **w**: Width.  
- **h**: Height.
- **fill**: if True, draw filled rectangle.

# `draw_circle(x0, y0, r, fill=False)`
Draw a circle using a midpoint algorithm.

#### Parameters:
- **x0, y0**: Centered coordinates
- **r**: Radius.  
- **fill**: if True, draw filled circle.


### Notes:
- The display uses an internal framebuffer.
- Drawing operations modify the buffer first.
- show() transfers the buffer to the OLED hardware.
- I2C locking is handled inside show() to prevent concurrent access.

### See also
- SSD1306 datasheet :https://cdn-shop.adafruit.com/datasheets/SSD1306.pdf
- SSD1306 Driver :https://github.com/TimHanewich/MicroPython-SSD1306/tree/master







