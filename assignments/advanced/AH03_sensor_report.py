"""AH03: 행 검증 순서를 지키고 구역별 측정/미측정과 문제를 분리한다."""
import argparse
import csv
import io
import json
import math
from pathlib import Path

BASE = Path(__file__).resolve().parent


def read_rows(path):
    text = Path(path).read_text(encoding="utf-8-sig")
    reader = csv.reader(io.StringIO(text), strict=True)
    header = next(reader, None)
    if not header or len(set(header)) != len(header) or not {"id", "area", "temperature"}.issubset(header):
        raise ValueError("입력파일 오류")
    return header, list(reader)


def validate_row(raw, header, accepted_ids):
    if len(raw) != len(header):
        return None, "열 개수 오류"
    row = dict(zip(header, raw))
    identifier, area = row["id"].strip(), row["area"].strip()
    if not identifier:
        return None, "번호 누락"
    if not area:
        return None, "구역 누락"
    if identifier in accepted_ids:
        return None, "번호 중복"
    temperature = row["temperature"].strip()
    try:
        value = None if not temperature else float(temperature)
        if value is not None and not math.isfinite(value):
            raise ValueError("유한한 숫자가 아님")
    except ValueError:
        return None, "온도 오류"
    return {"id": identifier, "area": area, "temperature": value}, None


def aggregate(header, rows):
    accepted, issues, seen = [], [], set()
    for line, raw in enumerate(rows, 2):
        row, reason = validate_row(raw, header, seen)
        if reason:
            issues.append({"line": line, "reason": reason})
        else:
            accepted.append(row)
            seen.add(row["id"])
    groups = {}
    for row in accepted:
        groups.setdefault(row["area"], []).append(row["temperature"])
    def summary(values):
        measured = [value for value in values if value is not None]
        return {"measured_count": len(measured), "missing_count": len(values) - len(measured),
                "average": round(sum(measured) / len(measured), 2) if measured else None}
    stats = summary([row["temperature"] for row in accepted])
    return {"input_count": len(rows), "accepted_count": len(accepted), **stats,
            "alerts": [row["id"] for row in accepted if row["temperature"] is not None and row["temperature"] >= 28],
            "areas": {area: summary(values) for area, values in groups.items()}, "issues": issues}


def save_report(report, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=BASE / "data/sensors.csv")
    parser.add_argument("--output", type=Path, default=BASE / "work/sensor_report.json")
    args = parser.parse_args()
    try:
        header, rows = read_rows(args.source)
        report = aggregate(header, rows)
        save_report(report, args.output)
    except (OSError, UnicodeError, ValueError, csv.Error):
        print("입력파일 오류")
        return 1
    print(f"입력 {report['input_count']} / 정상 {report['accepted_count']} / 오류 {len(report['issues'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
