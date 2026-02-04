# BUTTONS

## Detailed Description
This module provides a simple MicroPython API for reading the two push buttons available on the TKJHAT extension board used with the Raspberry Pi Pico (RP2040).

### Note:
The driver is intentionally designed with a **polling-based interface** to keep it easy to understand and suitable for teaching purposes.

---

## Hardware information

- Button type: Momentary push buttons
- Logic level: Active-high
- Pull-down resistors: Enabled in software
- Intended use: User input, control signals, simple interaction

---

## Default connections (TKJHAT)

| Signal   | MicroPython / Board | GPIO | Description        |
|---------|---------------------|------|--------------------|
| Button 1| Pin(2)              | 2    | User button 1      |
| Button 2| Pin(22)             | 22   | User button 2      |

---

## Usage example

```python
from buttons import Buttons
import time

buttons = Buttons()
buttons.init()

while True:
    if buttons.button1_pressed():
        print("Button 1 pressed")

    if buttons.button2_pressed():
        print("Button 2 pressed")

    if buttons.any_pressed():
        print("At least one button is pressed")

    time.sleep(0.1)
```

## Notes: 
- Buttons are configured as active-high
 - 1 means pressed
 - 0 means released
- Internal pull-down resistors are enabled to ensure stable readings
- Interrupt-based handling is intentionally not used to keep the implementation simple

# Buttons code documentation

## **class Buttons(button1_pin: int = 2, button2_pin: int = 22)**
Create a Buttons instance for accessing the TKJHAT buttons.

**Parameters:**
 - Button1_pin = GPIO pin for button 1 (default: GPIO 2)
 - Button2_pin = GPIO pin for button 2 (default: GPIO 22)

# Function Documentation

# `init()`
Initialize the buzzer.

### What it does:
 - Configures both button pins as digital inputs
 - Enables internal pull-down resistors


# `button1_pressed() -> bool`
Check the state of button 1.

### Returns:
 - True if button 1 is pressed.
 - False if not.

# `button2_pressed() -> bool`
Check the state of button 2.

### Returns:
 - True if button 2 is pressed.
 - False if not.

# `any_pressed() -> bool`
Check the state of both buttons.

### Returns:
 - True if button either button is pressed.
 - False if not.
