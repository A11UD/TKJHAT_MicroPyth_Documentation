from machine import Pin, I2C
import time

#Simple main to test functionality of LED, RGBLED, Buzzer, HDC2021, Buttons and SSD1306


# Drivers
from hdc2021 import HDC2021
from buzzer import Buzzer
from buttons import Buttons
from led import Led
from rgb_led import Rgb_led
from display import Display


i2c = I2C(0, sda=Pin(12), scl=Pin(13), freq=400_000)


# Initialize 


display = Display(i2c)
display.init()

sensor = HDC2021(i2c)
sensor.init()

buzzer = Buzzer()
buzzer.init()

buttons = Buttons()
buttons.init()

led = Led()
led.init()

rgb = Rgb_led()
rgb.init()


# Startup test

display.clear()
display.write_text("TKJHAT TEST")
display.show()

buzzer.play_tone(4000, 200)
led.blink(1)

rgb.write(255, 0, 0)
time.sleep(0.5)

rgb.write(0, 255, 0)
time.sleep(0.5)

rgb.write(0, 0, 255)
time.sleep(0.5)

rgb.write(0, 0, 0)

# Main loop

last_display = time.ticks_ms()

while True:

    # Button actions (event-style)
 
    if buttons.button1_pressed():
        display.clear()
        display.draw_circle(64, 32, 20, fill=False)
        display.show()

        buzzer.play_tone(3000, 200)
        rgb.write(255, 255, 0)
        time.sleep(1)

        display.clear(show=True)

    elif buttons.button2_pressed():
        display.clear()
        display.draw_rectangle(10, 10, 50, 30, fill=True)
        display.show()

        buzzer.play_tone(1500, 200)
        rgb.write(0, 255, 255)
        time.sleep(1)

        display.clear(show=True)

    else:
        rgb.write(0, 0, 0)

  
    #sensor display updated at (1 Hz)

    now = time.ticks_ms()
    if time.ticks_diff(now, last_display) >= 1000:
        temp = sensor.read_temperature()
        hum = sensor.read_humidity()

        display.clear()
        display.write_text_xy(0, 0, "HDC2021")
        display.write_text_xy(0, 16, "Temp: {:.1f} C".format(temp))
        display.write_text_xy(0, 32, "Hum : {:.1f} %".format(hum))
        display.show()

        last_display = now

    time.sleep(0.05)
