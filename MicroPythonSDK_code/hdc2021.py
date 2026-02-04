# hdc2021.py
# MicroPython driver for the HDC2021 Temperature & Humidity sensor
#
# Based on the TKJHAT Pico C SDK implementation
# I2C address: 0x40
#
# Features:
# - Continuous temperature + humidity measurement
# - 1 Hz sampling rate
# - 14-bit resolution
# - Threshold configuration
# - Same behavior as C SDK, but simpler syntax


import time


class HDC2021:

    # I2C address

    ADDRESS = 0x40

    # Register addresses

    TEMP_LOW = 0x00
    HUMID_LOW = 0x02

    CONFIG = 0x0E
    MEAS_CONFIG = 0x0F

    TEMP_THR_LOW = 0x13
    TEMP_THR_HIGH = 0x14
    HUMID_THR_LOW = 0x15
    HUMID_THR_HIGH = 0x16
    #In datasheet
    #TEMP_THR_LOW = 0x0A
    #TEMP_THR_HIGH = 0x0B
    #HUMID_THR_LOW = 0x0C
    #HUMID_THR_HIGH = 0xD


    # Constructor

    def __init__(self, i2c):
        self.i2c = i2c


    # Low-level I2C helpers

    def _read_u8(self, reg):
        """
        Read one byte from a register
        """
        return self.i2c.readfrom_mem(self.ADDRESS, reg, 1)[0]

    def _write_u8(self, reg, value):
        """
        Write one byte to a register
        """
        self.i2c.writeto_mem(self.ADDRESS, reg, bytes([value & 0xFF]))

    def _read_u16(self, reg):
        """
        Read two bytes (LSB first) and return a 16-bit value
        """
        data = self.i2c.readfrom_mem(self.ADDRESS, reg, 2)
        return data[1] * 256 + data[0]


    # Configuration functions 

    def reset(self):
        """
        Software reset:
        Set bit 7 of CONFIG register
        """
        config = self._read_u8(self.CONFIG)
        self._write_u8(self.CONFIG, config | 0x80)
        time.sleep_ms(50)

    def set_measurement_mode(self):
        """
        Enable temperature + humidity measurement
        (clear mode bits)
        """
        value = self._read_u8(self.MEAS_CONFIG)
        self._write_u8(self.MEAS_CONFIG, value & 0xF9)

    def set_rate_1hz(self):
        """
        Set automatic measurement rate to 1 Hz
        """
        config = self._read_u8(self.CONFIG)
        config = (config & 0x8F) | 0x50
        self._write_u8(self.CONFIG, config)

    def set_temp_resolution_14bit(self):
        """
        Set temperature resolution to 14-bit
        """
        value = self._read_u8(self.MEAS_CONFIG)
        self._write_u8(self.MEAS_CONFIG, value & 0x3F)

    def set_humidity_resolution_14bit(self):
        """
        Set humidity resolution to 14-bit
        """
        value = self._read_u8(self.MEAS_CONFIG)
        self._write_u8(self.MEAS_CONFIG, value & 0xCF)

    def trigger_measurement(self):
        """
        Start continuous measurement
        """
        value = self._read_u8(self.MEAS_CONFIG)
        self._write_u8(self.MEAS_CONFIG, value | 0x01)


    # Threshold configuration 

    def set_low_temp_threshold(self, temp_c):
        temp_c = max(-40.0, min(125.0, temp_c))
        value = int((temp_c + 40.0) * 256.0 / 165.0)
        value = max(0, min(255, value))
        self._write_u8(self.TEMP_THR_LOW, value)

    def set_high_temp_threshold(self, temp_c):
        temp_c = max(-40.0, min(125.0, temp_c))
        value = int((temp_c + 40.0) * 256.0 / 165.0)
        value = max(0, min(255, value))
        self._write_u8(self.TEMP_THR_HIGH, value)

    def set_low_humidity_threshold(self, humidity):
        humidity = max(0.0, min(100.0, humidity))
        value = int(humidity * 256.0 / 100.0)   
        value = max(0, min(255, value))
        self._write_u8(self.HUMID_THR_LOW, value)

    def set_high_humidity_threshold(self, humidity):
        humidity = max(0.0, min(100.0, humidity))
        value = int(humidity * 256.0 / 100.0)
        value = max(0, min(255, value))
        self._write_u8(self.HUMID_THR_HIGH, value)



    # Public API (student-facing)

    def init(self):
        """
        Initialize sensor 
        """
        self.reset()

        self.set_high_temp_threshold(50)
        self.set_low_temp_threshold(-30)
        self.set_high_humidity_threshold(100)
        self.set_low_humidity_threshold(0)

        self.set_measurement_mode()
        self.set_rate_1hz()
        self.set_temp_resolution_14bit()
        self.set_humidity_resolution_14bit()
        self.trigger_measurement()

    def read_temperature(self) -> float:
        """
        Read temperature in Celsius
        """
        base_temp = self._read_u16(self.TEMP_LOW)
        return (base_temp * 165.0 / 65536.0) - 40.0

    def read_humidity(self) -> float:
        """
        Read relative humidity in %
        """
        base_humidity = self._read_u16(self.HUMID_LOW)
        return base_humidity * 100.0 / 65536.0

    def stop(self):
        """
        Stop continuous measurement and reduce power
        """
        config = self._read_u8(self.CONFIG)
        config = config & 0x8F      # disable auto-measurement
        config = config & 0xF3      # disable heater + interrupt
        self._write_u8(self.CONFIG, config)
        meas = self._read_u8(self.MEAS_CONFIG)
        self._write_u8(self.MEAS_CONFIG, meas & 0xFE)
