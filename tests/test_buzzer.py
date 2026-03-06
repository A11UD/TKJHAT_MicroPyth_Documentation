import pytest
import buzzer

class FakePin:

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
        self._freq = freq
        self.duty = None
        self.deinited = False
        self.duty_change_spy = []
        FakePWM.created.append(self)

    def duty_u16(self, value):
        self.duty = value
        self.duty_change_spy.append(value)

    
    def freq(self, value=None):
        if value is None:
            return self._freq
        self._freq = value


    def deinit(self):
        self.deinited = True



@pytest.fixture
def fakes(monkeypatch):
    # Reset logs before each test
    FakePin.created = []
    FakePWM.created = []
    # Monkeypatch the names used inside buzzer module
    monkeypatch.setattr(buzzer, "Pin", FakePin)
    monkeypatch.setattr(buzzer, "PWM", FakePWM)
    return {"Pin": FakePin, "PWM": FakePWM}


# Patch time.sleep_ms()

@pytest.fixture
def patch_sleep_ms(monkeypatch):

    sleeps = []

    def fake_sleep_ms(ms):
        sleeps.append(ms)

    monkeypatch.setattr(buzzer.time, "sleep_ms", fake_sleep_ms, raising=False)
    return sleeps

# Tests

def test_init(fakes, patch_sleep_ms):
    buzzer_inst = buzzer.Buzzer()
    buzzer_inst.init()

    # After init(), there should be PWM instance created
    assert len(FakePWM.created) == 1

    # Check the PWM instance uses the correct pin
    assert FakePWM.created[0].pin.pin_address == buzzer.Buzzer.BUZZER_PIN


    # Check the PWM instance has duty cycle 0
    assert FakePWM.created[0].duty == 0


@pytest.mark.parametrize(
    "frequency_hz, duration_ms",
    [
        (0, 0),          
        (-3, 255),     
        (128, 64),      
        (10, 300),     
    ],
)

def test_play_tone(fakes, patch_sleep_ms, frequency_hz, duration_ms):
    buzzer_inst = buzzer.Buzzer()
    buzzer_inst.init()

    buzzer_inst.play_tone(frequency_hz, duration_ms)
    
    if duration_ms > 0 and frequency_hz > 0:

        # Assert the written frequency is correct
        assert FakePWM.created[0]._freq == frequency_hz

        # Assert the duty cycle is modified 
        assert FakePWM.created[0].duty_change_spy[2] == 32768
        assert FakePWM.created[0].duty_change_spy[3] == 0

        # Check that the sleep_ms is called
        assert patch_sleep_ms.count(duration_ms) == 1
    else:
        # Duty cycle should not be modified, when duration or frequency is negative or zero
        assert len(FakePWM.created[0].duty_change_spy) == 2

        # sleep should not be called
        assert len(patch_sleep_ms) == 0


def test_deinit(fakes, patch_sleep_ms):
    buzzer_inst = buzzer.Buzzer()
    buzzer_inst.init()

    buzzer_inst.deinit()
    assert FakePWM.created[0].deinited
 