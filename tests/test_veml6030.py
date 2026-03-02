import pytest
import veml6030


class FakeI2C:
   
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

def convert_to_lux(bits):

    luxVal_uncorrected = bits * 0.5376     
    if luxVal_uncorrected > 1000:
        luxVal = ((0.00000000000060135 * luxVal_uncorrected ** 4) - 
                    (0.0000000093924 * luxVal_uncorrected ** 3) + 
                    (0.000081488 * luxVal_uncorrected ** 2) + 
                    (1.0023 * luxVal_uncorrected)
                    )
        return luxVal

    return luxVal_uncorrected


@pytest.fixture
def i2c_and_sleep(monkeypatch):
    """
    Provide a FakeI2C instance and a spy for sleep_ms (recording delays).
    """
    i2c = FakeI2C()
    sleeps = []

    def fake_sleep_ms(ms):
        sleeps.append(ms)

    monkeypatch.setattr(veml6030.time, "sleep_ms", fake_sleep_ms, raising=False)
    return i2c, sleeps



def test_init(i2c_and_sleep):

    #Initialize the sensor
    i2c, sleeps = i2c_and_sleep
    sensor = veml6030.VEML6030(i2c)
    sensor.init()

    # Check the configuration was written correctly
    assert len(i2c.writes) == 1
    addr, payload, stop = i2c.writes[0]
    assert addr == sensor.ADDRESS
    assert payload == bytes([sensor.CONFIG, 0x00, 0x10])
    assert stop is True

    # Check sleep is called with 10ms
    assert sleeps[0] == 10

@pytest.mark.parametrize(
    "lsb, msb",
    [
        (0x20, 0x03),        # 800 <= 1000, no correction needed
        (0xe8, 0x0b)     # 3048 > 1000, polynomial correction should be used
    ],
)

def test_read(i2c_and_sleep, lsb, msb):

    #Initialize the sensor
    i2c, sleeps = i2c_and_sleep
    sensor = veml6030.VEML6030(i2c)
    sensor.init()

    # Simulate the sensor returning a 16 bit ambient light reading
    i2c.preload_read(sensor.ADDRESS, [lsb, msb])

    lux = sensor.read()

    # Check the command write (READ_DATA = 0x04) with stop=False
    addr, payload, stop = i2c.writes[1]
    assert addr == sensor.ADDRESS
    assert payload == bytes([sensor.READ_DATA])
    assert stop is False

    # Check the returned lux value is corrct and polynomial correction is used if the value > 1000
    expected_value = lsb | msb<<8
    assert lux == pytest.approx(convert_to_lux(expected_value))


def test_stop(i2c_and_sleep):

    #Initialize the sensor
    i2c, sleeps = i2c_and_sleep
    sensor = veml6030.VEML6030(i2c)
    sensor.init()

    sensor.stop()

    # Check the new configuration with stop bit was written correctly
    addr, payload, stop = i2c.writes[1]
    assert addr == sensor.ADDRESS
    assert payload == bytes([sensor.CONFIG, 0x01, 0x10])
    assert stop is True

    # Check sleep is called with 10ms
    assert len(sleeps) == 2
    assert sleeps[1] == 10
