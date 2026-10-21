# 장비 대여 실습의 작업 규칙

- Python 표준 라이브러리만 사용한다.
- 수량은 정확한 int, 0≤available≤total을 지킨다.
- 실패한 요청이나 잘못된 저장 파일을 자동으로 초기화하지 않는다.
- 변경 후 `python -m unittest discover -s projects/equipment-loan -v`를 저장소 루트에서 실행한다.
- 실제 실행 결과와 미확인 범위를 docs/handoff.md에 기록한다.
