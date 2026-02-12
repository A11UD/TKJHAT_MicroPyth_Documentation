from machine import Pin, I2C
import time

# Drivers
from bus_manager import I2CBusManager
from hdc2021 import HDC2021
from icm42670 import ICM42670
from buzzer import Buzzer
from buttons import Buttons
from led import Led
from rgb_led import Rgb_led
from display import Display


# -------------------------
# I2C setup
# -------------------------

i2c = I2C(0, sda=Pin(12), scl=Pin(13), freq=400_000)

# Bus manager only for selected drivers
bus = I2CBusManager(i2c)


# -------------------------
# Initialize drivers
# -------------------------

display = Display(bus)
display.init()

sensor = HDC2021(bus)
sensor.init()

# IMU still uses raw I2C (no locking added there)
imu = ICM42670(i2c)
imu.init()
imu.start_with_default_values()

buzzer = Buzzer()
buzzer.init()

buttons = Buttons()
buttons.init()

led = Led()
led.init()

rgb = Rgb_led()
rgb.init()


# -------------------------
# Startup test
# -------------------------

display.write_text("TKJHAT TEST")

buzzer.play_tone(4000, 200)
led.blink(1)

rgb.write(255, 0, 0)
time.sleep(0.5)

rgb.write(0, 255, 0)
time.sleep(0.5)

rgb.write(0, 0, 255)
time.sleep(0.5)

rgb.write(0, 0, 0)


# Brief IMU check
data = imu.read_sensor_data()

display.clear()
display.write_text_xy(0, 0, "ICM42670")

if data is None:
    display.write_text_xy(0, 16, "Read failed")
else:
    display.write_text_xy(0, 16, "OK")

time.sleep(1.0)


# -------------------------
# Main loop
# -------------------------

last_display = time.ticks_ms()
show_imu = False

while True:

    # -------------------------
    # Button actions
    # -------------------------

    if buttons.button1_pressed():

        display.clear()
        display.draw_circle(64, 32, 20, fill=False)

        buzzer.play_tone(3000, 200)
        rgb.write(255, 255, 0)
        time.sleep(1)

        display.clear()

    elif buttons.button2_pressed():

        display.clear()
        display.draw_rectangle(10, 10, 50, 30, fill=True)

        buzzer.play_tone(1500, 200)
        rgb.write(0, 255, 255)
        time.sleep(1)

        display.clear()

    else:
        rgb.write(0, 0, 0)

    # -------------------------
    # Sensor display (1 Hz)
    # -------------------------

    now = time.ticks_ms()

    if time.ticks_diff(now, last_display) >= 1000:

        if not show_imu:
            temp = sensor.read_temperature()
            hum = sensor.read_humidity()

            display.clear()
            display.write_text_xy(0, 0, "HDC2021")

            if temp is None or hum is None:
                display.write_text_xy(0, 16, "Read failed")
            else:
                display.write_text_xy(0, 16, "Temp: {:.1f} C".format(temp))
                display.write_text_xy(0, 32, "Hum : {:.1f} %".format(hum))

        else:
            d = imu.read_sensor_data()

            display.clear()
            display.write_text_xy(0, 0, "ICM42670")

            if d is None:
                display.write_text_xy(0, 16, "Read failed")
            else:
                ax, ay, az, gx, gy, gz, t = d
                display.write_text_xy(0, 16, "az: {:.2f} g".format(az))
                display.write_text_xy(0, 32, "gz: {:.1f} dps".format(gz))
                display.write_text_xy(0, 48, "t : {:.1f} C".format(t))

        show_imu = not show_imu
        last_display = now

    time.sleep(0.05)