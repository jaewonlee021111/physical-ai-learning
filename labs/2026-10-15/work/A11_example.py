from pathlib import Path
for name, action in [("파일", lambda: Path("definitely-missing.csv").read_text()), ("헤더", lambda: {}["temperature_c"]), ("값", lambda: float("뜨거움"))]:
    try:
        action()
    except (FileNotFoundError, KeyError, ValueError) as error:
        print(name, type(error).__name__)
