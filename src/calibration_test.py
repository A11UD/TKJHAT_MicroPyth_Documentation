from machine import I2C, Pin
import time, math
from bus_manager import I2CBusManager
from icm42670 import ICM42670

# ---- optional: bus recovery (helps after soft reboot) ----
def i2c_recover(scl_pin=13, sda_pin=12):
    scl = Pin(scl_pin, Pin.OUT, value=1)
    sda = Pin(sda_pin, Pin.IN)
    time.sleep_ms(5)
    for _ in range(9):
        scl.value(0); time.sleep_us(50)
        scl.value(1); time.sleep_us(50)
    time.sleep_ms(5)

def gyro_stats(imu, n=300, dt_ms=10):
    xs=[]; ys=[]; zs=[]
    for _ in range(n):
        d = imu.read_sensor_data()
        if d:
            _, _, _, gx, gy, gz, _ = d
            xs.append(gx); ys.append(gy); zs.append(gz)
        time.sleep_ms(dt_ms)
    if not xs:
        return None

    def mean_std(v):
        m = sum(v)/len(v)
        s2 = sum((x-m)*(x-m) for x in v)/len(v)
        return m, math.sqrt(s2)

    return mean_std(xs), mean_std(ys), mean_std(zs)

def print_stats(label, stats):
    if stats is None:
        print(label, "NO DATA")
        return
    (mx,sx),(my,sy),(mz,sz) = stats
    print(label)
    print("  gx mean/std: %.4f / %.4f dps" % (mx, sx))
    print("  gy mean/std: %.4f / %.4f dps" % (my, sy))
    print("  gz mean/std: %.4f / %.4f dps" % (mz, sz))

# ---- main ----
i2c_recover(13, 12)

i2c = I2C(0, sda=Pin(12), scl=Pin(13), freq=100_000)
print("I2C scan:", [hex(a) for a in i2c.scan()])

bus = I2CBusManager(i2c)
imu = ICM42670(bus)

rc = imu.init()
print("IMU init rc:", rc)
rc = imu.start_with_default_values()
print("IMU start rc:", rc)

# Make sure deadband is off for measurement
imu.set_gyro_deadband(0.0)

print("\nPlace the device STILL on the table.")
time.sleep(2)

before = gyro_stats(imu, n=300, dt_ms=10)
print_stats("\nBEFORE calibration:", before)

print("\nCalibrating... keep STILL.")
bias = imu.calibrateGyro(samples=800, settle_ms=2000, reject_if_abs_dps=5.0, sample_delay_ms=10)
print("Computed bias (dps):", imu.g_bias, "return:", bias)

after = gyro_stats(imu, n=300, dt_ms=10)
print_stats("\nAFTER calibration:", after)

print("\nNow enabling deadband = 0.5 dps (motion detection friendly).")
imu.set_gyro_deadband(0.5)

print("Printing 30 samples (should often be 0.0 when still):")
for _ in range(30):
    d = imu.read_sensor_data()
    if d:
        _, _, _, gx, gy, gz, t = d
        print("gx gy gz:", gx, gy, gz, "temp:", t)
    time.sleep_ms(100)