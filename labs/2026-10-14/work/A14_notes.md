# A14 · 오류 수정

예약어 in은 소문자다.

## 수정 diff
```diff
--- A14_broken.py
+++ A14_fixed.py
@@ -1,4 +1,4 @@
 temperatures = [22.5, 24.0, 23.5]
-for temperature_c In temperatures:
+for temperature_c in temperatures:
     print(temperature_c)
 print("완료")
```

정상·의도한 오류·수정·확장 4종을 실행한다. 실제 stdout/stderr는 evidence/debug-results.json에 보존한다. 정상/오류 입력은 공식 교안의 짧은 실습 예제이며 확장 해답은 새로 작성했다.
