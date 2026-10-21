# A11 · 오류 수정

if 조건 뒤에 콜론을 붙인다.

## 수정 diff
```diff
--- A11_broken.py
+++ A11_fixed.py
@@ -1,5 +1,5 @@
 temperature_c = 25.0
-if temperature_c > 24.0
+if temperature_c > 24.0:
     print("확인")
 else:
     print("정상")
```

정상·의도한 오류·수정·확장 4종을 실행한다. 실제 stdout/stderr는 evidence/debug-results.json에 보존한다. 정상/오류 입력은 공식 교안의 짧은 실습 예제이며 확장 해답은 새로 작성했다.
