# icm42670.py
# MicroPython driver for the ICM-42670-P IMU (accelerometer + gyroscope + temperature)
#
# I2C address: 0x69 (alternative: 0x68)
#
# Features:
# - Accelerometer + gyroscope configuration (ODR + full-scale range)
# - Simple “start with defaults” setup for exercises
# - Burst read of temperature + accel + gyro data
# - Returns scaled values in user-friendly units (g, dps, °C)
# - Minimal, course-friendly API and structure

import time


class ICM42670:
    # I2C addresses
    ADDRESS = 0x69
    ADDRESS_ALT = 0x68

    # Register addresses (User Bank 0)
    REG_SIGNAL_PATH_RESET = 0x02
    REG_WHO_AM_I = 0x75

    REG_PWR_MGMT0 = 0x1F
    REG_GYRO_CONFIG0 = 0x20
    REG_ACCEL_CONFIG0 = 0x21

    REG_SENSOR_DATA_START = 0x09  # temp + accel + gyro burst

    # Expected identity
    WHO_AM_I_RESPONSE = 0x67

    # Soft reset bit
    RESET_CONFIG_BITS = 0x10  # bit4

    # Output data rate codes (bits[3:0])
    ODR_25HZ = 0x0B
    ODR_50HZ = 0x0A
    ODR_100HZ = 0x09
    ODR_200HZ = 0x08
    ODR_400HZ = 0x07
    ODR_800HZ = 0x06
    ODR_1600HZ = 0x05

    # Accelerometer full-scale codes (placed to bits[6:5])
    ACCEL_FSR_2G = 0x03
    ACCEL_FSR_4G = 0x02
    ACCEL_FSR_8G = 0x01
    ACCEL_FSR_16G = 0x00

    # Default configuration
    ACCEL_ODR_DEFAULT = 100
    ACCEL_FSR_DEFAULT = 4
    GYRO_ODR_DEFAULT = 100
    GYRO_FSR_DEFAULT = 250

    def __init__(self, bus, address=ADDRESS):
        self.bus = bus
        self.address = address

        # Scale factors (LSB per unit)
        self.aRes = 8192.0   # for ±4g
        self.gRes = 131.0    # for ±250 dps

        # Calibration state (bias in user units: g and dps)
        self.g_bias = [0.0, 0.0, 0.0]
        self.a_bias = [0.0, 0.0, 0.0]

        # Optional: ignore tiny gyro noise for motion detection
        self.g_deadband_dps = 0.0

    # -------------------------
    # Low-level I2C helpers
    # -------------------------
    def _read_u8(self, reg):
        return self.bus.readfrom_mem(self.address, reg, 1)[0]

    def _write_u8(self, reg, value):
        self.bus.writeto_mem(self.address, reg, bytes([value & 0xFF]))

    def _read_bytes(self, reg, n):
        return self.bus.readfrom_mem(self.address, reg, n)

    @staticmethod
    def _to_i16(msb, lsb):
        v = (msb << 8) | lsb
        return v - 65536 if (v & 0x8000) else v

    # -------------------------
    # Internal helpers
    # -------------------------
    def _odr_bits(self, odr_hz):
        if odr_hz == 25:
            return self.ODR_25HZ
        if odr_hz == 50:
            return self.ODR_50HZ
        if odr_hz == 100:
            return self.ODR_100HZ
        if odr_hz == 200:
            return self.ODR_200HZ
        if odr_hz == 400:
            return self.ODR_400HZ
        if odr_hz == 800:
            return self.ODR_800HZ
        if odr_hz == 1600:
            return self.ODR_1600HZ
        return None

    def _accel_fsr_bits_and_scale(self, fsr_g):
        if fsr_g == 2:
            return self.ACCEL_FSR_2G, 16384.0
        if fsr_g == 4:
            return self.ACCEL_FSR_4G, 8192.0
        if fsr_g == 8:
            return self.ACCEL_FSR_8G, 4096.0
        if fsr_g == 16:
            return self.ACCEL_FSR_16G, 2048.0
        return None, None

    def _gyro_fsr_bits_and_scale(self, fsr_dps):
        # codes placed to bits[6:5]
        if fsr_dps == 250:
            return 0x03, 131.0
        if fsr_dps == 500:
            return 0x02, 65.5
        if fsr_dps == 1000:
            return 0x01, 32.8
        if fsr_dps == 2000:
            return 0x00, 16.4
        return None, None

    def _autodetect_address(self):
        for cand in (self.ADDRESS, self.ADDRESS_ALT):
            try:
                self.address = cand
                who = self._read_u8(self.REG_WHO_AM_I)
                if who == self.WHO_AM_I_RESPONSE:
                    return cand
            except OSError:
                pass
        return None

    # -------------------------
    # Public API
    # -------------------------
    def soft_reset(self):
        self._write_u8(self.REG_SIGNAL_PATH_RESET, self.RESET_CONFIG_BITS)
        time.sleep_ms(10)

    def init(self):
        """
        Initialize the IMU and verify device identity.

        The driver first autodetects the I2C address (0x68 / 0x69) by reading WHO_AM_I,
        then performs a soft reset on the detected address and re-checks WHO_AM_I.

        Returns 0 on success, negative on error.
        """
        try:
            addr = self._autodetect_address()
            if addr is None:
                return -1

            # Reset on the correct address
            self.soft_reset()

            who = self._read_u8(self.REG_WHO_AM_I)
            if who != self.WHO_AM_I_RESPONSE:
                return -2

            time.sleep_us(200)
            return 0
        except OSError:
            return -3

    def startAccel(self, odr_hz, fsr_g):
        """
        Configure accelerometer.
        Returns 0 on success, negative on error.
        """
        try:
            fsr_bits, aRes = self._accel_fsr_bits_and_scale(fsr_g)
            if fsr_bits is None:
                return -1

            odr_bits = self._odr_bits(odr_hz)
            if odr_bits is None:
                return -2

            self.aRes = aRes
            val = (fsr_bits << 5) | (odr_bits & 0x0F)
            self._write_u8(self.REG_ACCEL_CONFIG0, val)
            time.sleep_us(200)
            return 0
        except OSError:
            return -3

    def startGyro(self, odr_hz, fsr_dps):
        """
        Configure gyroscope.
        Returns 0 on success, negative on error.
        """
        try:
            fsr_bits, gRes = self._gyro_fsr_bits_and_scale(fsr_dps)
            if fsr_bits is None:
                return -1

            odr_bits = self._odr_bits(odr_hz)
            if odr_bits is None:
                return -2

            self.gRes = gRes
            val = (fsr_bits << 5) | (odr_bits & 0x0F)
            self._write_u8(self.REG_GYRO_CONFIG0, val)
            time.sleep_us(200)
            return 0
        except OSError:
            return -3

    def enable_accel_gyro_ln_mode(self):
        """
        Enable low-noise mode for accel and gyro.
        """
        try:
            self._write_u8(self.REG_PWR_MGMT0, 0x0F)
            time.sleep_us(200)
            return 0
        except OSError:
            return -1

    def start_with_default_values(self):
        """
        Convenience setup for typical exercises (low-noise mode + default ODR/FSR).
        Returns 0 on success, negative on error.
        """
        rc = self.enable_accel_gyro_ln_mode()
        if rc != 0:
            return rc

        rc = self.startAccel(self.ACCEL_ODR_DEFAULT, self.ACCEL_FSR_DEFAULT)
        if rc != 0:
            return rc

        rc = self.startGyro(self.GYRO_ODR_DEFAULT, self.GYRO_FSR_DEFAULT)
        if rc != 0:
            return rc

        return 0

    def calibrateGyro(self, dest2=None, samples=800, settle_ms=2000,
                    reject_if_abs_dps=5.0, sample_delay_ms=10):
        """
        Measure and apply gyroscope zero-rate bias (offset) while the device is stationary.

        The function collects multiple gyro samples, rejects samples that indicate motion,
        computes the mean bias for each axis in dps, and stores the result to self.g_bias.
        If dest2 is provided (a list of length 3), it is filled with [bx, by, bz].

        Returns:
            (bx, by, bz) on success, or None if not enough valid samples were collected.
        """

        old_g = self.g_bias[:]
        self.g_bias = [0.0, 0.0, 0.0]

        # settle/warm-up
        t0 = time.ticks_ms()
        while time.ticks_diff(time.ticks_ms(), t0) < settle_ms:
            self.read_sensor_data()
            time.sleep_ms(5)

        sx = sy = sz = 0.0
        good = 0

        for _ in range(samples):
            d = self.read_sensor_data()
            if d is None:
                continue

            ax, ay, az, gx, gy, gz, temp = d

            # reject samples if device is moving
            if (abs(gx) > reject_if_abs_dps or
                abs(gy) > reject_if_abs_dps or
                abs(gz) > reject_if_abs_dps):
                continue

            sx += gx
            sy += gy
            sz += gz
            good += 1
            time.sleep_ms(sample_delay_ms)

        if good < max(10, samples // 4):
            self.g_bias = old_g
            return None

        bx, by, bz = sx / good, sy / good, sz / good
        self.g_bias[0], self.g_bias[1], self.g_bias[2] = bx, by, bz

        if dest2 is not None:
            dest2[0], dest2[1], dest2[2] = bx, by, bz

        return bx, by, bz


    def calibrateAccel(self, dest1=None, samples=800, settle_ms=2000,
                   assume_up_axis="z", assume_up_sign=+1,
                   reject_if_abs_dps=5.0, sample_delay_ms=10):
        """
        Measure and apply accelerometer bias (offset) while the device is stationary
        in a known orientation.

        The function collects multiple accel samples, rejects samples that indicate motion,
        computes the mean measured acceleration, compares it against an expected gravity
        vector (±1 g along the selected axis), and stores the resulting bias to self.a_bias.
        If dest1 is provided (a list of length 3), it is filled with [bx, by, bz].

        Parameters:
            assume_up_axis: Axis expected to align with gravity ("x", "y", or "z").
            assume_up_sign: +1 if that axis should read +1 g, -1 if it should read -1 g.

        Returns:
            (bx, by, bz) on success, or None if not enough valid samples were collected.
        """

        old_a = self.a_bias[:]
        self.a_bias = [0.0, 0.0, 0.0]

        # settle/warm-up
        t0 = time.ticks_ms()
        while time.ticks_diff(time.ticks_ms(), t0) < settle_ms:
            self.read_sensor_data()
            time.sleep_ms(5)

        sx = sy = sz = 0.0
        good = 0

        for _ in range(samples):
            d = self.read_sensor_data()
            if d is None:
                continue

            ax, ay, az, gx, gy, gz, temp = d

            # reject if moving (gyro-based)
            if (abs(gx) > reject_if_abs_dps or
                abs(gy) > reject_if_abs_dps or
                abs(gz) > reject_if_abs_dps):
                continue

            sx += ax
            sy += ay
            sz += az
            good += 1
            time.sleep_ms(sample_delay_ms)

        if good < max(10, samples // 4):
            self.a_bias = old_a
            return None

        axm, aym, azm = sx / good, sy / good, sz / good

        # ideal gravity vector based on assumed orientation
        ideal = [0.0, 0.0, 0.0]
        axis_map = {"x": 0, "y": 1, "z": 2}
        idx = axis_map.get(assume_up_axis, 2)
        ideal[idx] = float(assume_up_sign) * 1.0  # 1g along that axis

        bx = axm - ideal[0]
        by = aym - ideal[1]
        bz = azm - ideal[2]

        self.a_bias[0], self.a_bias[1], self.a_bias[2] = bx, by, bz

        if dest1 is not None:
            dest1[0], dest1[1], dest1[2] = bx, by, bz

        return bx, by, bz


    def set_gyro_deadband(self, deadband_dps):
        self.g_deadband_dps = float(deadband_dps)

    def read_sensor_data(self):
        """
        Returns (ax, ay, az, gx, gy, gz, t)
        - accel in g
        - gyro in dps
        - temp in °C
        Returns None on I2C error.
        """
        try:
            raw = self._read_bytes(self.REG_SENSOR_DATA_START, 14)

            t_raw = self._to_i16(raw[0], raw[1])
            ax_raw = self._to_i16(raw[2], raw[3])
            ay_raw = self._to_i16(raw[4], raw[5])
            az_raw = self._to_i16(raw[6], raw[7])
            gx_raw = self._to_i16(raw[8], raw[9])
            gy_raw = self._to_i16(raw[10], raw[11])
            gz_raw = self._to_i16(raw[12], raw[13])

            t = (t_raw / 128.0) + 25.0

            ax = ax_raw / self.aRes
            ay = ay_raw / self.aRes
            az = az_raw / self.aRes

            gx = gx_raw / self.gRes
            gy = gy_raw / self.gRes
            gz = gz_raw / self.gRes

            # Apply calibration
            ax -= self.a_bias[0]
            ay -= self.a_bias[1]
            az -= self.a_bias[2]

            gx -= self.g_bias[0]
            gy -= self.g_bias[1]
            gz -= self.g_bias[2]

            # Optional deadband for motion detection
            db = self.g_deadband_dps
            if db > 0.0:
                if abs(gx) < db: gx = 0.0
                if abs(gy) < db: gy = 0.0
                if abs(gz) < db: gz = 0.0

            return ax, ay, az, gx, gy, gz, t

        except OSError:
            return None