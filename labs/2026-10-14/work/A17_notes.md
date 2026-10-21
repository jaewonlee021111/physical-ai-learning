# A17 · 오류 수정

초과 >와 이상 >=의 경계 차이를 지킨다.

## 수정 diff
```diff
--- A17_broken.py
+++ A17_fixed.py
@@ -1,6 +1,6 @@
 temperatures = [23.0, 24.0, 25.0]
 for temperature_c in temperatures:
-    if temperature_c >= 24.0:
+    if temperature_c > 24.0:
         print(temperature_c, "확인")
     else:
         print(temperature_c, "정상")
```

정상·의도한 오류·수정·확장 4종을 실행한다. 실제 stdout/stderr는 evidence/debug-results.json에 보존한다. 정상/오류 입력은 공식 교안의 짧은 실습 예제이며 확장 해답은 새로 작성했다.
