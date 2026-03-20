
import pytest
import time
import led as mod


# ---------------------------------------------------
# Fakes
# ---------------------------------------------------
class FakePin:

    # Keep a log of all created pins
    created = []

    # mimic the constatnt
    OUT = "out"

    def __init__(self, pin_id, mode=None):
        self.pin_id = pin_id
        self.mode = mode
        self.toggles = 0
        self.value_calls = []
        FakePin.created.append(self)

    def toggle(self):
        """Record toggle calls"""
        self.toggles += 1

    def value(self, v):
        """Record writes to .value()"""
        self.value_calls.append(v)


# ---------------------------------------------------
# Fixtures
# ---------------------------------------------------

@pytest.fixture
def fakes(monkeypatch):
    # Reset logs before each test
    FakePin.created = []
    # monkeypatch Pin() inside the led module
    monkeypatch.setattr(mod, "Pin", FakePin)
 
    # patch sleep_ms calls
    sleep_calls = []
    def fake_sleep(ms):
        sleep_calls.append(ms)

    monkeypatch.setattr(mod.time, "sleep_ms", fake_sleep, raising=False)

    return sleep_calls


# ---------------------------------------------------
# Tests
# ---------------------------------------------------

def init(fakes):
    led = mod.Led()
    led.init()

    # Pin was created
    assert len(FakePin.created) == 1
    pin = FakePin.created[0]
    assert pin.pin_id == mod.Led.LED_PIN
    assert pin.mode == FakePin.OUT
    assert led.pin is pin


def test_toggle(fakes):
    led = mod.Led()
    led.init()
    pin = FakePin.created[0]

    led.toggle()
    led.toggle()

    assert pin.toggles == 2


def test_set_status(fakes):
    led = mod.Led()
    led.init()
    pin = FakePin.created[0]

    led.set_status(True)
    led.set_status(False)

    assert pin.value_calls == [True, False]


def test_blink(fakes):
    led = mod.Led()
    led.init()
    pin = FakePin.created[0]
    sleeps = fakes

    led.blink(3)

    # Each blink does: toggle, sleep, toggle, sleep
    # For n blinks: 2*n toggles, 2*n sleeps
    assert pin.toggles == 3 * 2
    assert len(sleeps) == 3 * 2

    # Each sleep must be with TOGGLE_SLEEP_TIME
    assert all(ms == mod.Led.TOGGLE_SLEEP_TIME for ms in sleeps)

    # After blinking, LED should be forced OFF
    assert pin.value_calls[-1] is False

