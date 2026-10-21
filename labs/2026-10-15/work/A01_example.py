def temperature_status(value, threshold=24.0):
    if value is None:
        return "미측정"
    return "확인" if value > threshold else "정상"
print([temperature_status(value) for value in [22.5, None, 25.0]])
