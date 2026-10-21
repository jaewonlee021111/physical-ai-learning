from pathlib import Path
from log_checker import save
base = Path(__file__).resolve().parents[1]
print(save(base / "data/bad_readings.csv", base / "work"))
