import pytest
import veml6030


class FakeI2C:
    """
    Minimal fake for machine.I2C that:
      - records writes as (addr, bytes, stop)
      - records read requests as (addr, nbytes)
      - returns queued bytes for readfrom, or zeros if not queued
    """
    def __init__(self):
        self.writes = []
        self.read_queues = {}  # key: (addr, nbytes) -> list[bytes]

    def preload_read(self, addr, data_bytes):
        """Queue a read result for the next readfrom(addr, len(data_bytes)) call."""
        key = (addr, len(data_bytes))
        self.read_queues.setdefault(key, []).append(bytes(data_bytes))

    def writeto(self, addr, buf, stop=True):
        self.writes.append((addr, bytes(buf), stop))

    def readfrom(self, addr, nbytes):
        key = (addr, nbytes)
        queue = self.read_queues.get(key, [])
        if queue:
            return queue.pop(0)
        return bytes([0] * nbytes)


@pytest.fixture
def i2c_and_sleep(monkeypatch):
    """
    Provide a FakeI2C instance and a spy for sleep_ms (recording delays).
    """
    i2c = FakeI2C()
    sleeps = []

    def fake_sleep_ms(ms):
        sleeps.append(ms)

    # IMPORTANT: patch the symbol inside the module under test
    monkeypatch.setattr(veml6030, "sleep_ms", fake_sleep_ms)
    return i2c, sleeps

@pytest.fixture
def fake_i2c():
    return FakeI2C()


def test_init(fake_i2c):
    sensor = veml6030.VEML6030(fake_i2c)
    sensor.init()

    assert i2c.writes


def test_init_writes_config_and_sleeps(i2c_and_sleep):
    i2c, sleeps = i2c_and_sleep
    sensor = veml6030.VEML6030(i2c)

    sensor.init()

    # One 3-byte write: [CONFIG=0x00, LSB=0x00, MSB=0x10]
    assert i2c.writes, "No I2C writes performed"
    addr, payload, stop = i2c.writes[0]
    assert addr == mod.VEML6030.ADDRESS
    assert payload == bytes([mod.VEML6030.CONFIG, 0x00, 0x10])
    assert stop is True  # per write_u24

    # Sleep for 10ms
    assert sleeps == [10]


def test_read_returns_uncorrected_lux_when_below_threshold(i2c_and_sleep):
    i2c, _ = i2c_and_sleep
    sensor = mod.VEML6030(i2c)

    # Simulate the sensor returning a 16-bit little-endian value.
    # Choose 1000 (0x03E8): LSB first => [0xE8, 0x03]
    i2c.preload_read(mod.VEML6030.ADDRESS, [0xE8, 0x03])

    lux = sensor.read()

    # Check the command write (READ_DATA = 0x04) with stop=False
    addr, payload, stop = i2c.writes[0]
    assert addr == mod.VEML6030.ADDRESS
    assert payload == bytes([mod.VEML6030.READ_DATA])
    assert stop is False

    # Check the read call
    assert i2c.reads[0] == (mod.VEML6030.ADDRESS, 2)

    # Expected lux: bits * 0.5376 = 1000 * 0.5376 = 537.6 (below 1000, so no correction)
    assert lux == pytest.approx(537.6, rel=0, abs=1e-6)


def test_read_applies_polynomial_correction_when_above_threshold(i2c_and_sleep):
    i2c, _ = i2c_and_sleep
    sensor = mod.VEML6030(i2c)

    # Choose bits = 3000 (0x0BB8): little-endian -> [0xB8, 0x0B]
    i2c.preload_read(mod.VEML6030.ADDRESS, [0xB8, 0x0B])

    lux = sensor.read()

    # Uncorrected value first:
    bits = 3000
    uncorrected = bits * 0.5376
    assert uncorrected > 1000  # we are in correction branch

    # Expected with polynomial
    expected = ((0.00000000000060135 * uncorrected ** 4) -
                (0.0000000093924    * uncorrected ** 3) +
                (0.000081488        * uncorrected ** 2) +
                (1.0023             * uncorrected))
    # Float comparison: allow small tolerance
    assert lux == pytest.approx(expected, rel=1e-9, abs=1e-9)


def test_stop_writes_powerdown_and_sleeps(i2c_and_sleep):
    i2c, sleeps = i2c_and_sleep
    sensor = mod.VEML6030(i2c)

    sensor.stop()

    # One 3-byte write: [CONFIG=0x00, LSB=0x01, MSB=0x10]
    addr, payload, stop = i2c.writes[0]
    assert addr == mod.VEML6030.ADDRESS
    assert payload == bytes([mod.VEML6030.CONFIG, 0x01, 0x10])
    assert stop is True

    # Sleep for 10ms
    assert sleeps == [10]
