import csv
from pathlib import Path
path = Path(__file__).resolve().parents[1] / "data/readings.csv"
with path.open(encoding="utf-8-sig", newline="") as handle:
    rows = list(csv.DictReader(handle))
print(len(rows), rows[0]["sensor_id"], rows[0]["temperature_c"], type(rows[0]["temperature_c"]).__name__)
print(repr(rows[2]["temperature_c"]))
