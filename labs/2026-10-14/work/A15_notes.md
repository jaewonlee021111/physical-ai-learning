# A15 · 오류 수정

누적 변수는 반복 바깥에서 한 번 초기화한다.

## 수정 diff
```diff
--- A15_broken.py
+++ A15_fixed.py
@@ -1,6 +1,6 @@
 temperatures = [22.5, 25.0, 26.0]
+count = 0
 for temperature_c in temperatures:
-    count = 0
     if temperature_c > 24.0:
         count = count + 1
 print(count)
```

정상·의도한 오류·수정·확장 4종을 실행한다. 실제 stdout/stderr는 evidence/debug-results.json에 보존한다. 정상/오류 입력은 공식 교안의 짧은 실습 예제이며 확장 해답은 새로 작성했다.
