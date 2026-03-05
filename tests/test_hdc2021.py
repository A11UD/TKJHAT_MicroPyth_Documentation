import pytest
import hdc2021


class FakeI2C:

    def __init__(self):
        self.regs = {}   # key = device address, value = register map for the device
        self.writes = []  # (addr, reg, bytes_written)
        self.reads = []   # (addr, reg, n)

    def get_regmap(self, addr):
        return self.regs.setdefault(addr, {})

    def preload_u8(self, addr, reg, value):
        self.get_regmap(addr)[reg] = bytes([value & 0xFF])

    def preload_u16(self, addr, reg, value):
        low = value & 0xFF
        high = (value >> 8) & 0xFF
        self.get_regmap(addr)[reg] = bytes([low, high])

    def readfrom_mem(self, addr, reg, n):
        self.reads.append((addr, reg, n))
        regmap = self.get_regmap(addr)
        bytes_in_mem = regmap.get(reg, bytes([0] * n))
        if len(bytes_in_mem) < n:
            bytes_in_mem = bytes_in_mem + bytes([0] * (n - len(bytes_in_mem)))
        return bytes_in_mem[:n]

    def writeto_mem(self, addr, reg, buf):
        self.writes.append((addr, reg, bytes(buf)))
        self.get_regmap(addr)[reg] = bytes(buf)

@pytest.fixture
def i2c():
    return FakeI2C()

# Patching time.sleep_ms

@pytest.fixture
def patch_sleep_ms(monkeypatch):

    sleeps = []

    def fake_sleep_ms(ms):
        sleeps.append(ms)

    monkeypatch.setattr(hdc2021.time, "sleep_ms", fake_sleep_ms, raising=False)
    return sleeps


# --- Helpers for conversions ---

def temp_c_to_thr(temp_c):
    t = max(-40.0, min(125.0, temp_c))
    val = int((t + 40.0) * 256.0 / 165.0)
    return max(0, min(255, val))

def humid_to_thr(h):
    h = max(0.0, min(100.0, h))
    val = int(h * 256.0 / 100.0)
    return max(0, min(255, val))

def u16_to_temp_c(raw):
    return (raw * 165.0 / 65536.0) - 40.0

def u16_to_humid(raw):
    return raw * 100.0 / 65536.0


# tests

def test_init(i2c, patch_sleep_ms):
    sensor = hdc2021.HDC2021(i2c)
    sensor.init()

    # the values written in the configuration registers
    config = int.from_bytes(i2c.regs[sensor.ADDRESS][0x0E])
    meas_config = int.from_bytes(i2c.regs[sensor.ADDRESS][0x0F])

    # Check that time.sleep_ms() was called
    assert len(patch_sleep_ms) == 1
    assert patch_sleep_ms[0] == 50

    # Assert the default configuration was written correctly
    assert config & 0xf0 == 0xd0
    assert meas_config == 0x01

    # The values written in the treshold registers   
    temp_high = i2c.regs[sensor.ADDRESS][0x14]
    temp_low = i2c.regs[sensor.ADDRESS][0x13]
    humidity_high = i2c.regs[sensor.ADDRESS][0x16]
    humidity_low = i2c.regs[sensor.ADDRESS][0x15]

    # check that the default tresholds are set
    assert int.from_bytes(temp_high) == temp_c_to_thr(50)
    assert int.from_bytes(temp_low) == temp_c_to_thr(-30)
    assert int.from_bytes(humidity_high) == humid_to_thr(100)
    assert int.from_bytes(humidity_low) == humid_to_thr(0)


@pytest.mark.parametrize("raw", [0, 1000, 30000, 65535])

def test_read_temperature(i2c, raw, patch_sleep_ms):
    sensor = hdc2021.HDC2021(i2c)
    sensor.init()

    # Simulate the sensor writing temperature values 
    i2c.preload_u16(sensor.ADDRESS, 0x00, raw)

    # Check that read_temperature() returns the correct values
    t = sensor.read_temperature()
    assert t == pytest.approx(u16_to_temp_c(raw))


@pytest.mark.parametrize("raw", [0, 1000, 30000, 65535])

def test_read_humidity(i2c, raw, patch_sleep_ms):
    sensor = hdc2021.HDC2021(i2c)
    sensor.init()

     # Simulate the sensor writing humidity values
    i2c.preload_u16(sensor.ADDRESS, 0x02, raw)

    # Check that read_humidity() returns the correct values
    h = sensor.read_humidity()
    assert h == pytest.approx(u16_to_humid(raw))


def test_stop(i2c, patch_sleep_ms):
    sensor = hdc2021.HDC2021(i2c)
    sensor.init()

    sensor.stop()

    # the values written in the configuration registers
    config = int.from_bytes(i2c.regs[sensor.ADDRESS][0x0E])
    meas_config = int.from_bytes(i2c.regs[sensor.ADDRESS][0x0F])

    # Assert that the configuration was changed to disable auto-measurement, heater and interrupt 
    # and the measurement trigger bit was set to 0
    assert config & 0x7c == 0x00
    assert meas_config == 0x00




