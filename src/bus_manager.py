# bus_manager.py
# Centralized I2C Bus Manager for TKJHAT
#
# Purpose:
# - Prevent simultaneous I2C access
# - Centralize hardware communication
# - Prepare for thread-safe locking
# - Improve system robustness
#
# Usage:
#   bus = I2CBusManager(i2c)
#   sensor = HDC2021(bus)
#   display = Display(bus)


try:
    import _thread
    THREADING_AVAILABLE = True
except ImportError:
    THREADING_AVAILABLE = False


class I2CBusManager:
    

    def __init__(self, i2c):
        self.i2c = i2c

        # Create lock if threading is available
        if THREADING_AVAILABLE:
            self._lock = _thread.allocate_lock()
        else:
            self._lock = None


    def _acquire(self):
        if self._lock is not None:
            self._lock.acquire()

    def _release(self):
        if self._lock is not None:
            self._lock.release()



    def readfrom_mem(self, addr, reg, nbytes):
        self._acquire()
        try:
            return self.i2c.readfrom_mem(addr, reg, nbytes)
        finally:
            self._release()

    def writeto_mem(self, addr, reg, data):
       
        self._acquire()
        try:
            self.i2c.writeto_mem(addr, reg, data)
        finally:
            self._release()

    def readfrom(self, addr, nbytes):
        self._acquire()
        try:
            return self.i2c.readfrom(addr, nbytes)
        finally:
            self._release()

    def writeto(self, addr, data, stop=True):
        self._acquire()
        try:
            self.i2c.writeto(addr, data, stop)
        finally:
            self._release()