from A05_example import status
cases = [(23.9, "정상"), (24.0, "정상"), (24.1, "확인"), (None, "미측정"), (0.0, "정상")]
for value, expected in cases:
    actual = status(value)
    assert actual == expected
    print(value, expected, actual)
