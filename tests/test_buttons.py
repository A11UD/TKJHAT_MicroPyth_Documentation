import pytest
import buttons


class FakePin:

    # Keep a log of all created pins
    created = []

    # mimic the constatnts
    IN = "IN"
    PULL_DOWN = "PULL_DOWN"

    def __init__(self, pin_address, mode=None, pull=None):
        self.pin_address = pin_address
        self.mode = mode
        self.pull = pull
        self._value = 0
        FakePin.created.append(self)

    def value(self):
        return self._value
    
@pytest.fixture
def fake_pin(monkeypatch):
    # Reset logs before each test
    FakePin.created = []
    # Monkeypatch the names used inside buzzer module
    monkeypatch.setattr(buttons, "Pin", FakePin)
    return {"Pin": FakePin}

# tests

def test_init(fake_pin):
    buttons_inst = buttons.Buttons()
    buttons_inst.init()

    # Check that the pins for both buttons are created with right values
    assert len(FakePin.created) == 2
    assert FakePin.created[0].mode == FakePin.IN
    assert FakePin.created[1].mode == FakePin.IN
    assert FakePin.created[0].pull == FakePin.PULL_DOWN
    assert FakePin.created[1].pull == FakePin.PULL_DOWN
    assert (FakePin.created[0].pin_address == buttons_inst.BUTTON1_PIN) or (FakePin.created[1].pin_address == buttons_inst.BUTTON1_PIN)
    assert (FakePin.created[0].pin_address == buttons_inst.BUTTON2_PIN) or (FakePin.created[1].pin_address == buttons_inst.BUTTON2_PIN)


def test_button1_pressed_and_button2_pressed(fake_pin):
    buttons_inst = buttons.Buttons()
    buttons_inst.init()

    # The function should return False when not pressed
    assert not buttons_inst.button1_pressed()
    assert not buttons_inst.button2_pressed()

    # simulate the buttons being pressed
    FakePin.created[0]._value = 1
    FakePin.created[1]._value = 1

    assert buttons_inst.button1_pressed()
    assert buttons_inst.button2_pressed()