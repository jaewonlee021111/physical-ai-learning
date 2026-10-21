from pathlib import Path
base = Path(__file__).resolve().parents[1]
print((base / "data/notice.txt").read_text(encoding="utf-8").strip())
try:
    (base / "data/not-found.txt").read_text()
except FileNotFoundError as error:
    print(type(error).__name__)
