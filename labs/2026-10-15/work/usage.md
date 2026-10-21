# 로그 검사기 실행

저장소 루트에서 `python labs/2026-10-15/work/log_checker.py` 실행. 입력은 data/bad_readings.csv, 결과는 work/check_summary.json과 check_issues.json이다. 다른 입력은 첫 인자로 지정하고 `--output`으로 결과 폴더를 지정한다. 온도 변환·범위·미측정을 확인하며 실제 센서 정확도와 안전은 확인하지 않는다.
