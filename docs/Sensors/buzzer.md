# BUZZER

## Detailed Description
This module provides a simple API for the Buzzer in TKJHAT extension board connected to Raspberry Pi Pico (RP2040).
This driver uses **PWM** to generate tones with configurable frequency and duration.

### Note:
The implementation is intentionally made simple and blocking, suitable for teaching purposes.

## Hardware information:

- Buzzer model: PKM13EPYH4000-A0
- Type: Passive piezoelectric buzzer
- Recommended frequency: 4 kHz = maximum acoustic output

### Default connections (TKJHAT)
| Signal              | MicroPython / Board              | GPIO | Description                               |
|---------------------|----------------------------------|------|-------------------------------------------|
| Buzzer              | Pin(17)                          | 17   | Buzzer output                             |

### Usage example:

```python
from buzzer import Buzzer
import time

buzzer = Buzzer()
buzzer.init()

buzzer.play_tone(4000, 300)   # 4 kHz tone for 300 ms
time.sleep(1)
buzzer.play_tone(2000, 500)   # 2 kHz tone for 500 ms
```

## Notes: 
- The buzzer is passive, so frequency affects the sound.
- The play_tone() function is **blocking**:
    - The CPU waits until the tone has finished playing.
- Suitable for short sounds, not continuous audio.


# Buzzer code documentation
**class Buzzer(pin: int = 17)**

Create a buzzer instance
**Parameters**
- **pin:** GPIO pin connected to the buzzer

# Function Documentation

# `init()`
Intialize the buzzer.

### What it does:
 - Initializes the PWM on the buzzer pin.
 - Puts buzzer to off state.


# `play_tone(frequency_hz: int, duration_ms: int)`

Play a tone on the buzzer.

### Parameters:
 - **frequency_hz:** Set tone frequency
 - **duration_ms:** Set duration in ms

### Notes:
 - Sets duty-cycle to around 50%
 - Values ≤ 0 are ignored
 - Function blocks until playback is finished


# `turn_off()`
Turn the buzzer off.

### What it does:
 - Turns the duty cycle to 0.

# `deinit()`
Deinitialize the buzzer.

### What it does:
 - Disables the PWM peripheral.


## See also
- **Murata PKM13EPYH4000-A0:** https://pim.murata.com/en-global/pim/details/?partNum=PKM13EPYH4000-A0
- **Micropython PWM documentation:** https://docs.micropython.org/en/latest/library/machine.PWM.html
