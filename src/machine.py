# Fake machine module for avoiding ModuleNotFoundError when running tests with modules using machine

class PWM:
    def __init__(self):
        pass

    def duty_u16(self, value):
        pass

    def deinit(self):
        pass

class Pin:

    def __init__(self):
        pass

class I2C:
    def __init__(self):
        pass

    def preload_read(self, addr, data_bytes):
        pass

    def writeto(self, addr, buf, stop=True):
        pass

    def readfrom(self, addr, nbytes):
        pass