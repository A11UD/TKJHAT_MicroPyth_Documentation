# LED
## Detailed Description
The module provides API for controlling the 

### Default connections (TKJHAT)

| Signal    | GPIO |
| -------- | ------- |
| led | 14     |

### Notes
- The blink() funktion is **blocking**
### Usage example:
```python
from led import Led

led = Led()
led.init()

led.blink(3)

```
## RGB LED code documentation
class Led()

## Function documentation
## `init()`
Initialize the led

**What it does:**
- Creates a Pin object for the LED using the pin number LED_PIN (14).
- Configures the pin as an output.

## `toggle() -> None`
Toggle the LED on/off  

**What it does:**  
- Checks that the led is initialized and if yes, switches the LED from on->off or off->on.

## `set_status(status: bool): -> None`
Sets the LED explicitly on or off  
**What it does:**  
- Ensures the pin was initialized and sets the pin value to hig or low 
**Parameters:**  
- status: boolean. True->led on, False->led off  

## `blink(n: int): -> None`  
Blink the LED n times.  
**What it does:**  
- Checks that the led is initialized
- The LED is toggled on and off n times, with a 120 ms (TOGGLE_SLEEP_TIME) delay between toggles.
**Parameters:**  
- n: int, number of blinks