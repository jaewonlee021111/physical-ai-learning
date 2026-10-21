import csv
from pathlib import Path
base = Path(__file__).resolve().parents[1]
with (base / "data/bad_readings.csv").open(encoding="utf-8-sig", newline="") as handle:
    reader = csv.DictReader(handle)
    fields, rows = reader.fieldnames, list(reader)
for row in rows:
    if row["sensor_id"] == "S05" and row["measured_at"] == "2026-10-08 10:05":
        row["temperature_c"] = "23.5"
with (base / "work/bad_readings_work.csv").open("w", encoding="utf-8", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)
print("S05만 23.5로 수정. S06은 원문 보존·확인 필요.")
