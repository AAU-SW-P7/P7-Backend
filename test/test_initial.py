"""Initial test file."""

def func(x):
    """Sample function to be tested."""
    return x * 2


def test_func():
    """Test the sample function.
    assert: Check if func works correctly.
    """
    assert func(3) == 6
    assert func(-1) == -2
    assert func(0) == 0
