# 설계

데이터는 id·name·total·available을 가진 객체의 배열이다. id는 중복되지 않는 비어 있지 않은 문자열이고 수량은 정확한 int이며 0≤available≤total을 유지한다.

app.py는 인자 해석·화면 출력을 담당한다. inventory.py의 validate/load/change/save/transact가 검사·복원·복사본 변경·임시 파일 교체·처리 흐름을 담당한다. 실패한 변경은 저장 함수에 도달하지 않는다. 저장 실패가 일어나면 임시 파일은 정리하고 기존 파일을 유지한다.

흐름: 입력 → JSON 복원·스키마 검사 → ID·재고 경계 확인 → 복사본 변경 → 같은 폴더의 임시 파일 저장 → os.replace → 결과 출력. 프로세스 사이 경쟁은 이 실습 범위 밖이다.
