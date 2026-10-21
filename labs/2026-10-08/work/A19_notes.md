# A19 · 문법 오류와 자료형 오류 고치기

## 작성한 결과
문법 복구 뒤에도 id는 문자열, temperature_c는 숫자 또는 null, active는 bool인지 검사한다. "false" 문자열은 False가 아니고 "null" 문자열은 None이 아니다. fixed JSON과 extra JSON을 다시 읽어 각 필드의 타입을 확인한다.

공개 교안 활동에 대한 재현 풀이. 사람과의 짝 검토는 별도 진행 항목이다.
