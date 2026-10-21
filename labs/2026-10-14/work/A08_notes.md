# A08 · 오류 수정

단위 글자와 숫자 값은 분리한다.

## 수정 diff
```diff
--- A08_broken.py
+++ A08_fixed.py
@@ -1,3 +1,3 @@
-raw = "22.5도"
+raw = "22.5"
 temperature_c = float(raw)
 print(temperature_c + 1)
```

정상·의도한 오류·수정·확장 4종을 실행한다. 실제 stdout/stderr는 evidence/debug-results.json에 보존한다. 정상/오류 입력은 공식 교안의 짧은 실습 예제이며 확장 해답은 새로 작성했다.
