from app.analyzers.endpoint_security import _as_bool


def test_as_bool_supports_powershell_numeric_values():
    assert _as_bool(1) is True
    assert _as_bool(0) is False


def test_as_bool_supports_strings_and_booleans():
    assert _as_bool(True) is True
    assert _as_bool(False) is False
    assert _as_bool("1") is True
    assert _as_bool("0") is False
    assert _as_bool("enabled") is True
    assert _as_bool("disabled") is False