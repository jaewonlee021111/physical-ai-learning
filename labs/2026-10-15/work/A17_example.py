import json
from pathlib import Path
from log_checker import save
base = Path(__file__).resolve().parents[1]
results = []
for filename in ["readings.csv", "bad_readings.csv", "empty_readings.csv", "missing_readings.csv"]:
    result = save(base / "data" / filename, base / "work/comparison" / Path(filename).stem)
    results.append(result)
    print(result)
(base / "work/A17_comparison.json").write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
