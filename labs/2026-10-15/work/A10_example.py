def parse(raw):
    return None if raw.strip() == "" else float(raw)
for raw in ["22.5", "", "0.0", "뜨거움"]:
    try:
        print(repr(raw), parse(raw))
    except ValueError:
        print(repr(raw), "ValueError: 실제값 확인 필요")
