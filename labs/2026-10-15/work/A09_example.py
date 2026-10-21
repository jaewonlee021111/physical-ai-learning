import json
from pathlib import Path
result = {"count": 5, "missing": 1}
path = Path(__file__).resolve().parent / "output_summary.json"
path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
assert json.loads(path.read_text()) == result
print(result["count"], result["missing"])
