from pathlib import Path
from log_checker import check
path = Path(__file__).resolve().parents[1] / "data/bad_readings.csv"
summary, issues = check(path)
assert summary["total"] == summary["accepted"] + len(issues)
assert summary["accepted"] == summary["numeric"] + summary["missing"]
print(summary)
