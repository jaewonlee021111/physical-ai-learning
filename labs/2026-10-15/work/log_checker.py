"""A16/A17: 수업의 0~50 입력 규칙으로 센서 CSV를 검사한다."""
import argparse
import csv
import json
import math
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]


def parse_temperature(raw):
    if raw.strip() == "":
        return None
    value = float(raw)
    if not math.isfinite(value) or not 0 <= value <= 50:
        raise ValueError("범위 오류")
    return value


def check(source):
    accepted, issues, count = [], [], 0
    with Path(source).open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not {"sensor_id", "temperature_c"}.issubset(reader.fieldnames or []):
            raise ValueError("필수 헤더 누락")
        for line, row in enumerate(reader, 2):
            count += 1
            try:
                if None in row or row["temperature_c"] is None:
                    raise ValueError("열 개수 오류")
                value = parse_temperature(row["temperature_c"])
                accepted.append(value)
            except ValueError as error:
                issues.append({"line": line, "sensor_id": row.get("sensor_id"),
                               "raw": row.get("temperature_c"), "reason": str(error)})
    numeric = [v for v in accepted if v is not None]
    summary = {"source": Path(source).name, "total": count, "accepted": len(accepted),
               "missing": len(accepted) - len(numeric), "numeric": len(numeric),
               "issue_count": len(issues), "average": round(sum(numeric) / len(numeric), 2) if numeric else None}
    return summary, issues


def save(source, output):
    summary, issues = check(source)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    for name, value in [("check_summary.json", summary), ("check_issues.json", issues)]:
        (output / name).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", nargs="?", type=Path, default=BASE / "data/bad_readings.csv")
    parser.add_argument("--output", type=Path, default=BASE / "work")
    args = parser.parse_args()
    print(json.dumps(save(args.source, args.output), ensure_ascii=False))
