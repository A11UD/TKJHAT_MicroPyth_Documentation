import pytest
import rgb_led


class FakePin:
    IN = "IN"  # mimic the constant

    # Keep a log of all created pins
    created = []

    def __init__(self, pin_address, mode=None):
        self.pin_address = pin_address
        self.mode = mode
        FakePin.created.append(self)

class FakePWM:
    # Keep a log of all created PWM instances
    created = []

    def __init__(self, pin, freq=None):
        self.pin = pin
        self.freq = freq
        self.duty = None
        self.deinited = False
        FakePWM.created.append(self)

    def duty_u16(self, value):
        self.duty = value

    def deinit(self):
        self.deinited = True


@pytest.fixture
def fakes(monkeypatch):
    # Reset logs before each test
    FakePin.created = []
    FakePWM.created = []
    # Monkeypatch the names used inside rgb_led module
    monkeypatch.setattr(rgb_led, "Pin", FakePin)
    monkeypatch.setattr(rgb_led, "PWM", FakePWM)
    return {"Pin": FakePin, "PWM": FakePWM}



def test_init(fakes):
    # Create rgb_led instance
    led = rgb_led.Rgb_led()

    # Initialize the rgb_led
    led.init()

    # After init(), there should be 3 PWM instances
    assert len(FakePWM.created) == 3

    # Check the PWM instances use correct pins
    assert FakePWM.created[0].pin.pin_address == led.RGB_LED_R
    assert FakePWM.created[1].pin.pin_address == led.RGB_LED_G
    assert FakePWM.created[2].pin.pin_address == led.RGB_LED_B

    # Check the PWM instances have right frequency
    for pwm in FakePWM.created:
        assert pwm.freq == led.RGB_FREQ

    assert led.initialized


def expected_duty(x):
    # Clamp, invert, convert to 16-bit duty cycle (0-65535)
    if x < 0:
        x = 0
    elif x > 255:
        x = 255
    inv = 255 - x
    return inv * inv

@pytest.mark.parametrize(
    "r,g,b",
    [
        (0, 0, 0),           # all off
        (255, 255, 255),     # all on
        (128, 64, 200),      # mid values
        (-10, 300, 255),     # clamping
    ],
)

def test_write(fakes, r, g, b):
    # Create rgb_led instance
    led = rgb_led.Rgb_led()
    led.init()

    # Try writing values r, g, b
    led.write(r, g, b)

    # Check that the written pwm duties are correct
    duties = [pwm.duty for pwm in FakePWM.created]
    assert duties[0] == expected_duty(r)
    assert duties[1] == expected_duty(g)
    assert duties[2] == expected_duty(b)

def test_stop(fakes):
    led = rgb_led.Rgb_led()
    led.init()

    led.stop()

    # PWM channels should be deinitlialized
    for pwm in FakePWM.created:
        assert pwm.deinited

    # Pins should be set to input (three new Pin instances with mode=IN)
    assert len(FakePin.created) >= 3
    last_three = FakePin.created[-3:]
    pin_addresses = [p.pin_address for p in last_three]
    assert set(pin_addresses) == {led.RGB_LED_R, led.RGB_LED_G, led.RGB_LED_B}
    assert all(p.mode == FakePin.IN for p in last_three)

    assert not led.initialized


