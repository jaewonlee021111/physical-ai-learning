# 공식 과제 6개 · 구현과 실행

공식 10/14 기초 3개·10/15 심화 3개 명세에 맞춰 작성했다. 입력·오류·출력 형식을 테스트로 확인한다. 각 명세 원문은 [curriculum.json](../curriculum.json)의 assignments에 보존했다.

| 과제 | 구현 | 실행 |
| --- | --- | --- |
| HW01 트리 | 3~15 높이 재입력, 잎과 `|` 줄기 | `python assignments/basic/HW01_tree.py` |
| HW02 좌석 | 5좌석 예약·취소·중복·잘못된 번호 | `python assignments/basic/HW02_seats.py` |
| HW03 측정 분석 | 정수 범위·done·개수·합계·평균·최대·최소·기준 초과 | `python assignments/basic/HW03_measurements.py` |
| AH01 도형 | JSON 설정 검사·트리/다이아몬드·텍스트 저장 | `python assignments/advanced/AH01_shapes.py` |
| AH02 영속 예약 | JSON 복원·bool 검사·성공 직후 저장·손상 보존 | `python assignments/advanced/AH02_persistent_seats.py` |
| AH03 센서 보고서 | 순서 있는 행 검사·중복·그룹 평균·경고·문제 줄 | `python assignments/advanced/AH03_sensor_report.py` |

명령은 저장소 루트에서 실행한다. 기초 과제는 안내 프롬프트 없이 명세의 입력을 받는다. 예를 들어 HW02에 `1`, `2`, `3`, `0`을 차례로 입력하면 현황 확인 → 3번 좌석 예약 → 종료다.

심화 과제는 파일 옆 data에서 입력을 읽고 work에 결과를 쓴다. AH01/AH03의 실제 생성 결과도 work에 포함했다. 예약 상태는 개인 실행 상태이므로 Git에 고정하지 않고 별도 프로세스 테스트로 저장·복원을 검증했다. `--state`로 시험용 경로를 지정할 수 있다.

`python -m unittest discover -s tests -v`로 공식 기초 예시 출력과 오류·경계·파일 보존을 검증한다. 이전 examples/tree.py는 여러 트리 가로 출력용 추가 예제이고, 공식 HW01 명세에 맞춘 파일은 assignments/basic/HW01_tree.py다.
