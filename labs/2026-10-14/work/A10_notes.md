# A10 · 오류 수정

비교는 ==, 대입은 =다.

## 수정 diff
```diff
--- A10_broken.py
+++ A10_fixed.py
@@ -1,2 +1,2 @@
 temperature_c = 24.0
-print(temperature_c = 24.0)
+print(temperature_c == 24.0)
```

정상·의도한 오류·수정·확장 4종을 실행한다. 실제 stdout/stderr는 evidence/debug-results.json에 보존한다. 정상/오류 입력은 공식 교안의 짧은 실습 예제이며 확장 해답은 새로 작성했다.
