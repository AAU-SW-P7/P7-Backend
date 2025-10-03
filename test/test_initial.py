def func(x):
    return x * 2


def test_func():
    assert func(3) == 6
    assert func(-1) == -2
    assert func(0) == 0


def address():
    return "123 Main St, Anytown, USA"

def test_address():
    assert address() == "123 Main St, Anytown, USA"    