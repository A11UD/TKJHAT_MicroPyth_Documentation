import pytest
import sys
import importlib


class Fake_Bus_Manager:

    def __init__(self):
        self.aquire_count = 0
        self.release_count = 0
        self.i2c = object()

    def _acquire(self):
        self.aquire_count+=1

    def _release(self):
        self.release_count+=1


class Fake_SSD1306:
    def __init__(self, width, height, i2c, addr=0x3C, external_vcc=False):
        self.i2c = i2c
        self.addr = addr
        self.temp = bytearray(2)
        self.write_list = [b"\x40", None]  # Co=0, D/C#=1

        self.calls = []

    
    def _record(self, name, *args):
        self.calls.append((name, args))

    def poweron(self):
        self._record("poweron")

    def poweroff(self):
        self._record("poweroff")

    def fill(self, color):
        self._record("fill", color)

    def show(self):
        self._record("show")

    def text(self, text, x, y):
        self._record("text", text, x, y)
    
    def line(self, x0, y0, x1, y1):
        self._record("line", x0, y0, x1, y1)

    def hline(self, x, y, w, c):
        self._record("hline", x, y, w, c)

    def fill_rect(self, x, y, w, h, c):
        self._record("fill_rect", x, y, w, h, c)

    def rect(self, x, y, w, h, c):
        self._record("rect", x, y, w, h, c)
    
    def pixel(self, px, py, c):
        self._record("pixel", px, py, c)



class SSD1306ModuleStub:
    """
    Mimics the 'ssd1306' module with a SSD1306_I2C factory returning Fake_SSD1306.
    """
    def __init__(self, factory):
        self.factory = factory
        self.last_args = None
        self.last_oled = None

    def SSD1306_I2C(self, width, height, i2c, addr):
        self.last_args = (width, height, i2c, addr)
        self.last_oled = self.factory(width, height, i2c, addr)
        return self.last_oled


class TimeStub:
    """Provides sleep_ms like MicroPython's time module and records the last sleep."""
    def __init__(self):
        self.slept_ms = None

    def sleep_ms(self, ms):
        self.slept_ms = ms


@pytest.fixture
def import_display_with_fakes(monkeypatch, *, module_name='display'):
    """
    Import the display module fresh while stubbing 'ssd1306' and 'time'.
    Returns: (display_module, bus, ssd_stub, oled)
    """
    
    # Ensure fresh import of display module
    if "display" in sys.modules:
        del sys.modules["display"]

    # Prepare bus and ssd1306 stub
    bus = Fake_Bus_Manager()

    def oled_factory(width, height, i2c, addr):
        return Fake_SSD1306(width, height, i2c, addr)

    ssd_stub = SSD1306ModuleStub(factory=oled_factory)
    sys.modules['ssd1306'] = ssd_stub

    # import display as mod
    mod = importlib.import_module("display")

    # patch time
    time_stub = TimeStub()
    monkeypatch.setattr(mod, 'time', time_stub, False)

    return mod, bus, time_stub



# Tests

def test_init(import_display_with_fakes):
    mod, bus, time = import_display_with_fakes
    display = mod.Display(bus)
    display.init()

    #check that display is powered on 
    assert ("poweron", ()) in display.oled.calls

    #Check that display is cleared
    assert ("fill", (0,)) in display.oled.calls
    assert ("show", ()) in display.oled.calls

    # Check that the lock is used
    assert bus.aquire_count == 2
    assert bus.release_count == 2


def test_power_on(import_display_with_fakes):
    mod, bus, time = import_display_with_fakes
    display = mod.Display(bus)
    display.init()
    display.power_on()

    # Assert that oled.poweron() is called after initialization
    assert display.oled.calls[-1] == ("poweron", ())

    # Check that the lock is used
    assert bus.aquire_count == 3
    assert bus.release_count == 3


def test_power_off(import_display_with_fakes):
    mod, bus, time = import_display_with_fakes
    display = mod.Display(bus)
    display.init()
    display.power_off()

    # Assert that oled.poweroff() is called
    assert display.oled.calls[-1] == ("poweroff", ())

    # Check that the lock is used
    assert bus.aquire_count == 3
    assert bus.release_count == 3


def test_write_text_xy_empty_text(import_display_with_fakes):
    mod, bus, time = import_display_with_fakes
    display = mod.Display(bus)
    display.init()
    display.write_text_xy(1, 7, "")
    
    # Trying to write empty text should be no op
    assert not ("text", ("", 1, 7)) in display.oled.calls


@pytest.mark.parametrize("delay", [0, 30])
def test_write_text_xy(import_display_with_fakes, delay):
    mod, bus, time = import_display_with_fakes
    display = mod.Display(bus)
    display.init()
    display.write_text_xy(1, -7, "some text", delay)

    # Check that oled.text is called and negative value is clamped
    assert ("text", ("some text", 1, 0)) in display.oled.calls

    # Assert that oled.show is called after buffering the text
    assert display.oled.calls[-1] == ("show", ())

    # Check that the lock is used
    assert bus.aquire_count == 3
    assert bus.release_count == 3

    # If delay>0, time.sleep_ms should be called
    if delay > 0:
       assert time.slept_ms == delay


def test_write_text_empty_text(import_display_with_fakes):
    mod, bus, time = import_display_with_fakes
    display = mod.Display(bus)
    display.init()
    display.write_text("")

    # Trying to write empty text should be no op
    assert not ("text", ("", 8, 24)) in display.oled.calls


@pytest.mark.parametrize("delay", [0, 30])
def test_write_text(import_display_with_fakes, delay):
    mod, bus, time = import_display_with_fakes
    display = mod.Display(bus)
    display.init()
    display.write_text("some text", delay)

    # Check that display is cleared and oled.text is called using default centered position
    assert display.oled.calls.count(("fill", (0,))) == 2     # init() also calls oled.fill, therefore 2 occurrences expected
    assert ("text", ("some text", 8, 24)) in display.oled.calls

    # Assert that oled.show is called after buffering the text
    assert display.oled.calls[-1] == ("show", ())

    # Check that the lock is used
    assert bus.aquire_count == 3
    assert bus.release_count == 3

    # If delay>0, time.sleep_ms should be called
    if delay > 0:
       assert time.slept_ms == delay


def test_draw_line(import_display_with_fakes):
    mod, bus, time = import_display_with_fakes
    display = mod.Display(bus)
    display.init()
    display.draw_line(1, 9, 5, 24)

    assert ("line", (1, 9, 5, 24)) in display.oled.calls
    assert display.oled.calls.count(("show", ())) == 2

    # Check that the lock is used
    assert bus.aquire_count == 3
    assert bus.release_count == 3


@pytest.mark.parametrize("fill", [True, False])
def test_draw_rectangle_filled(import_display_with_fakes, fill):
    mod, bus, time = import_display_with_fakes
    display = mod.Display(bus)
    display.init()
    display.draw_rectangle(1, 2, 3, 4, fill)

    if fill:
        assert ("fill_rect", (1, 2, 3, 4, 1)) in display.oled.calls
    else:
        assert ("rect", (1, 2, 3, 4, 1)) in display.oled.calls

    assert display.oled.calls.count(("show", ())) == 2

    # Check that the lock is used
    assert bus.aquire_count == 3
    assert bus.release_count == 3


def test_draw_circle_nonpositive_radius(import_display_with_fakes):
    mod, bus, time = import_display_with_fakes
    display = mod.Display(bus)
    display.init()
    display.draw_circle(2, 16, 0)

    # Should be no op, no oled.pixel() and oled.hline() calls
    assert len([c for c in display.oled.calls if c[0] in {"pixel", "hline"}]) == 0

@pytest.mark.parametrize("fill", [True, False])
def test_draw_circle(import_display_with_fakes, fill):
    mod, bus, time = import_display_with_fakes
    display = mod.Display(bus)
    display.init()
    display.draw_circle(2, 16, 3, fill)

    # oled.pixel should be called several times
    assert len([c for c in display.oled.calls if c[0] in {"pixel"}]) > 1

    # oled.show is called only once in draw_circle (and once in init())
    assert display.oled.calls.count(("show", ())) == 2

    # If the circle is filled, hline is called several times
    if fill:
        assert len([c for c in display.oled.calls if c[0] in {"hline"}]) > 1
    else:
        assert len([c for c in display.oled.calls if c[0] in {"hline"}]) == 0


def test_draw_circle_r1_exact_points(import_display_with_fakes):
    mod, bus, time = import_display_with_fakes
    display = mod.Display(bus)
    display.init()
    display.draw_circle(10, 10, 1, fill=False)

    expected = {
        (11, 10), (10, 11), (9, 10), (10, 9)
    }
    pixels = {(name_args[1][0], name_args[1][1]) for name_args in display.oled.calls if name_args[0] == "pixel"}
    print(expected)
    print("------------")
    print(pixels)
    assert expected.issubset(pixels)  # some implementations may place diagonals for r=1
