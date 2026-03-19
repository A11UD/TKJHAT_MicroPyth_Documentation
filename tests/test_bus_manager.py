import pytest
import builtins
import importlib
import sys
import time
import threading

# ----------------------------
# Test utilities and stubs
# ----------------------------

class LockStub:
    """A minimal lock stub to track acquire/release calls."""
    def __init__(self):
        self.acquire_count = 0
        self.release_count = 0
        self.acquired = False

    def acquire(self):
        self.acquire_count += 1
        self.acquired = True

    def release(self):
        self.release_count += 1
        self.acquired = False


class ThreadModuleStub:
    """Stub for the `_thread` module."""
    def __init__(self, lock: LockStub):
        self._lock = lock

    def allocate_lock(self):
        return self._lock


class FakeI2C:
    """Stub for an I2C object with call capturing, simulated error throwing and concurrent calls detection"""
    def __init__(self, raise_exeption=False):
        self.calls = []
        self.raise_exeption = raise_exeption

    def _record(self, name, *args, **kwargs):
        self.calls.append((name, args, kwargs))

    def readfrom_mem(self, addr, reg, nbytes):
        self._record('readfrom_mem', addr, reg, nbytes)
        if self.raise_exeption:
            raise RuntimeError("I2C bus error")
        # default: return bytes of zeros
        return bytes([0] * nbytes)

    def writeto_mem(self, addr, reg, data):
        self._record('writeto_mem', addr, reg, data)
        if self.raise_exeption:
            raise RuntimeError("I2C bus error")


    def readfrom(self, addr, nbytes):
        self._record('readfrom', addr, nbytes)
        if self.raise_exeption:
            raise RuntimeError("I2C bus error")
        return bytes([0] * nbytes)

    def writeto(self, addr, data, stop=True):
        self._record('writeto', addr, data, stop)
        if self.raise_exeption:
            raise RuntimeError("I2C bus error")
        


def import_bus_manager_with_fakes(monkeypatch, fail_import=False):
    """
    Import the bus_manager module, simulating either presence of `_thread` or raising ImportError.
    - fail_import: if True, make import of '_thread' raise ImportError.
    Returns: (module, lock_stub or None)
    """
    # Ensure fresh import of bus_manager module
    sys.modules.pop("bus_manager", None)

    # Control '_thread' availability
    if fail_import:
        # Make import of '_thread' raise ImportError by intercepting __import__
        real_import = builtins.__import__

        # Evrything else gets imported normally, but _thread now trows an ImportError
        def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
            if name == "_thread":
                raise ImportError("_thread not available")
            return real_import(name, globals, locals, fromlist, level)
        
        # Pytest patches Python’s global import function with fake_import
        monkeypatch.setattr(builtins, "__import__", fake_import)

        # Ensures _thread is not already loaded
        sys.modules.pop('_thread', None)
        lock_stub = None
    else:
        # Provide a stubbed _thread module
        lock_stub = LockStub()
        sys.modules['_thread'] = ThreadModuleStub(lock_stub)

    # Import bus_manager
    mod = importlib.import_module("bus_manager")
    return mod, lock_stub


# ----------------------------
# I2CBusManager tests when threading is available
# ----------------------------

def test_threading_available_creates_lock(monkeypatch):
    mod, lock_stub = import_bus_manager_with_fakes(monkeypatch, fail_import=False)
    i2c = FakeI2C()
    bus_manager = mod.I2CBusManager(i2c)
    # When threading is available, a lock should be allocated
    assert bus_manager._lock is not None


@pytest.mark.parametrize(
    "method, args, expected_call, expected_return",
    [
        ("readfrom_mem", (0x40, 0x01, 3), ('readfrom_mem', (0x40, 0x01, 3), {}), b"\x00\x00\x00"),
        ("writeto_mem", (0x40, 0x02, b"\xAA\xBB"), ('writeto_mem', (0x40, 0x02, b"\xAA\xBB"), {}), None),
        ("readfrom", (0x40, 2), ('readfrom', (0x40, 2), {}), b"\x00\x00"),
        ("writeto", (0x40, b"\x01\x02", True), ('writeto', (0x40, b"\x01\x02", True), {}), None),
    ]
)
def test_i2c_methods_use_lock(monkeypatch, method, args, expected_call, expected_return):
    mod, lock_stub = import_bus_manager_with_fakes(monkeypatch, fail_import=False)
    i2c = FakeI2C()
    bus_manager = mod.I2CBusManager(i2c)

    # Call the bus_manager method (readfrom_mem, writeto_mem, readfrom or writeto)
    result = getattr(bus_manager, method)(*args)

    # Lock acquire/release exactly once
    assert lock_stub.acquire_count == 1
    assert lock_stub.release_count == 1
    # I2C called correctly
    assert i2c.calls[-1] == expected_call
    # Return value propagated
    assert result == expected_return


def test_release_happens_on_exception(monkeypatch):
    mod, lock_stub = import_bus_manager_with_fakes(monkeypatch, fail_import=False)
    i2c = FakeI2C(raise_exeption=True)
    bus_manager = mod.I2CBusManager(i2c)

    with pytest.raises(RuntimeError, match="I2C bus error"):
        bus_manager.readfrom(0x40, 4)

    # Even after exception, lock must be released
    assert lock_stub.acquire_count == 1
    assert lock_stub.release_count == 1


@pytest.mark.parametrize(
    "method, args",
    [
        ("readfrom_mem", (0x40, 0x01, 3)),
        ("writeto_mem", (0x40, 0x02, b"\xAA\xBB")),
        ("readfrom", (0x40, 2)),
        ("writeto", (0x40, b"\x01\x02", True)),
    ]
)
def test_thread_safety_under_concurrency(monkeypatch, method, args):
    """
    This test verifies thread-safety by detecting whether
    two threads ever call bus_managers i2c methods concurrently
    """

    mod, lock_stub = import_bus_manager_with_fakes(monkeypatch, fail_import=False)
    i2c = FakeI2C()
    bus = mod.I2CBusManager(i2c)

    # Shared state for detecting overlap INSIDE the critical section
    overlap_flag = {"inside": False, "overlap": False}

    # Functions used to wrap the critical section
    def enter_critical():
        if overlap_flag["inside"]:
            overlap_flag["overlap"] = True
        overlap_flag["inside"] = True

    def exit_critical():
        overlap_flag["inside"] = False

    # Wrap all bus-manager I2C methods to detect overlap
    def wrap_method(method):
        def wrapped(*args, **kwargs):
            enter_critical()
            try:
                return method(*args, **kwargs)
            finally:
                exit_critical()
        return wrapped

    # Wrap all public I2C operations
    monkeypatch.setattr(bus, "readfrom_mem", wrap_method(bus.readfrom_mem))
    monkeypatch.setattr(bus, "readfrom",     wrap_method(bus.readfrom))
    monkeypatch.setattr(bus, "writeto_mem",  wrap_method(bus.writeto_mem))
    monkeypatch.setattr(bus, "writeto",      wrap_method(bus.writeto))

    # Worker threads repeatedly performing I2C operations
    def worker():
        for _ in range(200):
            getattr(bus, method)(*args)
            time.sleep(0.00001)  # simulate slow operation

    # Start two threads
    t1 = threading.Thread(target=worker)
    t2 = threading.Thread(target=worker)
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    # If the lock works, overlap must never occur
    assert overlap_flag["overlap"] is False, "Concurrent critical-section overlap detected!"


# ----------------------------
# I2CBusManager tests when threading is NOT available
# ----------------------------

def test_no_threading_lock_is_none(monkeypatch):
    mod, lock_stub = import_bus_manager_with_fakes(monkeypatch, fail_import=True)
    assert mod.THREADING_AVAILABLE is False

    i2c = FakeI2C()
    bus_manager = mod.I2CBusManager(i2c)

    # No lock should be created
    assert bus_manager._lock is None  


def test_calls_work_without_lock(monkeypatch):
    mod, lock_stub = import_bus_manager_with_fakes(monkeypatch, fail_import=True)
    i2c = FakeI2C()
    bus_manager = mod.I2CBusManager(i2c)

    # All methods should work without using lock
    out1 = bus_manager.readfrom_mem(0x40, 0x00, 2)
    bus_manager.writeto_mem(0x40, 0x01, b"\xAA")
    out2 = bus_manager.readfrom(0x40, 3)
    bus_manager.writeto(0x40, b"\x01\x02", stop=False)

    # Return values as per stub defaults
    assert out1 == b"\x00\x00"
    assert out2 == b"\x00\x00\x00"

    # assert that i2c calls are recorded correctly
    assert i2c.calls == [
        ('readfrom_mem', (0x40, 0x00, 2), {}),
        ('writeto_mem', (0x40, 0x01, b'\xAA'), {}),
        ('readfrom', (0x40, 3), {}),
        ('writeto', (0x40, b'\x01\x02', False), {}),
    ]
