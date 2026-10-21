from pathlib import Path
from log_checker import check
base = Path(__file__).resolve().parents[1]
summary, issues = check(base / "data/readings.csv")
print("실행 안내")
print("python labs/2026-10-15/work/log_checker.py")
print("검사 범위: 온도 변환·0~50 범위·미측정 구별. 장비 정확도·실제 안전은 미검증.")
