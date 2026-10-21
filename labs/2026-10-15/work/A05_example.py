def status(value):
    if value is None:
        return "미측정"
    return "확인" if value > 24.0 else "정상"
if __name__ == "__main__":
    for value in [22.5, None, 24.0]:
        print(status(value))
