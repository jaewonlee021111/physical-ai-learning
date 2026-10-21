"""가상 센서 CSV를 검사해 원문과 상태를 JSON으로 보존한다."""
import argparse
import csv
import json
import math
from pathlib import Path


def classify(raw, minimum=0.0, maximum=35.0):
    if minimum > maximum:
        raise ValueError("최솟값은 최댓값보다 클 수 없습니다.")
    if raw is None or not raw.strip():
        return None, "미측정"
    try:
        value = float(raw)
    except ValueError:
        return None, "잘못된 숫자"
    if not math.isfinite(value):
        return None, "잘못된 숫자"
    return value, "정상" if minimum <= value <= maximum else "범위 밖"


def convert(source, destination):
    records = []
    with Path(source).open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        required = {"sensor_id", "timestamp", "value", "unit"}
        if not required.issubset(reader.fieldnames or []):
            raise ValueError("필수 CSV 헤더가 누락되었습니다.")
        for row in reader:
            if None in row or any(row[key] is None for key in required):
                raise ValueError("CSV 행의 열 개수를 확인하세요.")
            value, status = classify(row["value"])
            records.append({"sensor_id": row["sensor_id"], "timestamp": row["timestamp"],
                            "raw_value": row["value"], "value": value,
                            "unit": row["unit"], "status": status})
    normal = [row["value"] for row in records if row["status"] == "정상"]
    result = {"sample_data": True, "range": {"minimum": 0, "maximum": 35},
              "count": len(records), "normal_count": len(normal),
              "normal_mean": sum(normal) / len(normal) if normal else None,
              "records": records}
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", nargs="?", type=Path,
                        default=Path(__file__).resolve().parents[1] / "data" / "readings.csv")
    parser.add_argument("--output", type=Path, default=Path("output/sensor-report.json"))
    args = parser.parse_args()
    try:
        result = convert(args.source, args.output)
    except (OSError, ValueError, csv.Error) as error:
        parser.exit(1, f"처리 실패: {error}\n")
    print(f"{result['count']}개 처리 / 정상 {result['normal_count']}개 → {args.output}")


if __name__ == "__main__":
    main()

