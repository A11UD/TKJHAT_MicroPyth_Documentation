# RGB LED
## Detailed Description
The module provides API for controlling the common anode RGB LED on TKJHAT extencion board. The RGB LED is driven by PWM on each color channel r, g and b.

### Default connections (TKJHAT)

| Signal    | GPIO |
| -------- | ------- |
| RGB red | 18     |
| RGB green | 19     |
| RGB blue | 20     |

### Notes
- The PWM frequency is 480 Hz 

### Usage example:
```python
from rgb_led import Rgb_led
import time

rgb = Rgb_led()
rgb.init()

rgb.write(255, 0, 0) # Set color to red
time.sleep(2)
rgb.write(255, 255, 0) # Set color to yellow
time.sleep(2)
rgb.stop() 
```
## RGB LED code documentation

class Rgb_led() creates an rgb led instance.

## Function documentation
## `init()`
Initialize the rgb led  

**What it does:**
- Creates GPIO pin objects for color channels red, green and blue
- Wraps the pins with PWM controllers so its duty cycle can be varied to control brightness of the color channel.
- Sets a flag `initialized` to True.  

## `write(r: int, g: int, b: int) -> None`
Set color for rgb led using values in range 0-255 (0 = off, 255 = full on)  

**Parameters:**  
- r: red intensity (0-255, 0 = off, 255 = full on)
- g: green intensity (0-255, 0 = off, 255 = full on)
- b: blue intensity (0-255, 0 = off, 255 = full on)  

**What it does:**  
- Ensures values are in range 0-255.
- Inverts the values, because the rgb led is wired as common anode.
- Converts the inverted values linearly to a 16-bit duty cycle.
- Finally sets the inverted and converted values for red, green and blue.

## `stop() -> None`
Disable the PWM output for the rgb pins  

**What it does:**  
- Sets the rgb led off.
- Disables the PWM output
- Sets the pins to input state. This ensures the pins are in Hi-Z state and prevents any unintended LED glow.

## See also
- **Micropython PWM documentation:** https://docs.micropython.org/en/latest/library/machine.PWM.html
## Open issues
In the original TKJHAT SDK documentation, channel values are described as 0 = full on and 255 = off. However, the actual sdk.c implementation inverts this behavior so that 255 = full on and 0 = off.  In this module, 255 = full on and 0 = off, because it matches how the original SDK actually works and is more intuitive to use.