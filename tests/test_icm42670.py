import pytest
import icm42670

class FakeBus:
    """
    Minimal fake that mimics I2CBusManager methods used by ICM42670:
    - readfrom_mem(addr, reg, nbytes)
    - writeto_mem(addr, reg, data)
    """
    def __init__(self):
        self.writes = []  # list of (addr, reg, bytes)
        self.read_queues = {}  # key: (addr, reg, nbytes) -> list[bytes]

    def preload_read_mem(self, addr, reg, data_bytes):
        key = (addr, reg, len(data_bytes))
        self.read_queues.setdefault(key, []).append(bytes(data_bytes))

    def writeto_mem(self, addr, reg, data):
        self.writes.append((addr, reg, bytes(data)))

    def readfrom_mem(self, addr, reg, nbytes):
        key = (addr, reg, nbytes)
        q = self.read_queues.get(key, [])
        if q:
            return q.pop(0)
        return bytes([0] * nbytes)


@pytest.fixture
def bus_and_time(monkeypatch):
    """
    Provide FakeBus and patch time.sleep_ms/us so tests run fast and deterministically.
    """
    bus = FakeBus()

    def fake_sleep_ms(_ms):  # no-op
        return None

    def fake_sleep_us(_us):  # no-op
        return None

    monkeypatch.setattr(icm42670.time, "sleep_ms", fake_sleep_ms, raising=False)
    monkeypatch.setattr(icm42670.time, "sleep_us", fake_sleep_us, raising=False)

    # Also patch ticks to make settle loops deterministic (settle_ms can be set to 0 in tests)
    monkeypatch.setattr(icm42670.time, "ticks_ms", lambda: 0, raising=False)
    monkeypatch.setattr(icm42670.time, "ticks_diff", lambda a, b: a - b, raising=False)

    return bus


def _i16_to_be(v):
    v &= 0xFFFF
    return [(v >> 8) & 0xFF, v & 0xFF]


def test_main_features(bus_and_time):
    bus = bus_and_time
    imu = icm42670.ICM42670(bus)

    # ---------- 1) init(): autodetect + reset + WHO_AM_I re-check ----------
    # Make WHO_AM_I succeed on 0x69 only (first read for autodetect, second read after reset)
    bus.preload_read_mem(0x69, imu.REG_WHO_AM_I, [imu.WHO_AM_I_RESPONSE])
    bus.preload_read_mem(0x69, imu.REG_WHO_AM_I, [imu.WHO_AM_I_RESPONSE])

    assert imu.init() == 0
    assert imu.address == 0x69
    assert (0x69, imu.REG_SIGNAL_PATH_RESET, bytes([imu.RESET_CONFIG_BITS])) in bus.writes

    # ---------- 2) start_with_default_values(): LN mode + config writes ----------
    bus.writes.clear()
    assert imu.start_with_default_values() == 0

    # Check key writes exist (don’t overfit to exact ordering beyond essentials)
    assert (imu.address, imu.REG_PWR_MGMT0, bytes([0x0F])) in bus.writes
    assert any(w[1] == imu.REG_ACCEL_CONFIG0 for w in bus.writes)
    assert any(w[1] == imu.REG_GYRO_CONFIG0 for w in bus.writes)

    # ---------- 3) read_sensor_data(): scaling + bias + deadband ----------
    # Prepare one burst:
    # temp raw 0 => 25C
    # ax_raw 8192 => 1g (at aRes=8192)
    # gz_raw 131  => 1 dps (at gRes=131)
    raw = []
    raw += _i16_to_be(0)       # temp
    raw += _i16_to_be(8192)    # ax
    raw += _i16_to_be(0)       # ay
    raw += _i16_to_be(0)       # az
    raw += _i16_to_be(0)       # gx
    raw += _i16_to_be(0)       # gy
    raw += _i16_to_be(131)     # gz
    bus.preload_read_mem(imu.address, imu.REG_SENSOR_DATA_START, raw)

    imu.g_bias = [0.0, 0.0, 0.6]     # subtract 0.6 dps from gz
    imu.a_bias = [0.0, 0.0, 0.0]
    imu.set_gyro_deadband(0.5)       # clamp |g|<0.5 to 0

    d = imu.read_sensor_data()
    assert d is not None
    ax, ay, az, gx, gy, gz, t = d

    assert ax == pytest.approx(1.0)
    assert t == pytest.approx(25.0)
    # 1.0 - 0.6 = 0.4 < deadband 0.5 => 0.0
    assert gz == pytest.approx(0.0)

    # ---------- 4) calibrateGyro(): computes mean bias ----------
    # Feed repeated stationary samples with gx=1, gy=2, gz=3 dps via bursts.
    # Use settle_ms=0 and sample_delay_ms=0 to keep it fast.
    bus.read_queues.clear()

    def burst_for_g(gx_dps, gy_dps, gz_dps):
        gx_raw = int(gx_dps * imu.gRes)
        gy_raw = int(gy_dps * imu.gRes)
        gz_raw = int(gz_dps * imu.gRes)

        r = []
        r += _i16_to_be(0)        # temp
        r += _i16_to_be(0)        # ax
        r += _i16_to_be(0)        # ay
        r += _i16_to_be(0)        # az
        r += _i16_to_be(gx_raw)   # gx
        r += _i16_to_be(gy_raw)   # gy
        r += _i16_to_be(gz_raw)   # gz
        return r

    # Preload enough reads for samples (warm-up loop is skipped by settle_ms=0)
    for _ in range(60):
        bus.preload_read_mem(imu.address, imu.REG_SENSOR_DATA_START, burst_for_g(1.0, 2.0, 3.0))

    bias = imu.calibrateGyro(samples=50, settle_ms=0, reject_if_abs_dps=5.0, sample_delay_ms=0)
    assert bias is not None
    bx, by, bz = bias

    assert bx == pytest.approx(1.0, abs=0.05)
    assert by == pytest.approx(2.0, abs=0.05)
    assert bz == pytest.approx(3.0, abs=0.05)
    assert imu.g_bias[0] == pytest.approx(1.0, abs=0.05)
    assert imu.g_bias[1] == pytest.approx(2.0, abs=0.05)
    assert imu.g_bias[2] == pytest.approx(3.0, abs=0.05)