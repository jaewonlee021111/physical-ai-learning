# A01 · 오류 수정

줄 순서가 실행 순서를 결정한다.

## 수정 diff
```diff
--- A01_broken.py
+++ A01_fixed.py
@@ -1,3 +1,3 @@
-print("출고")
 print("입고")
 print("검사")
+print("출고")
```

정상·의도한 오류·수정·확장 4종을 실행한다. 실제 stdout/stderr는 evidence/debug-results.json에 보존한다. 정상/오류 입력은 공식 교안의 짧은 실습 예제이며 확장 해답은 새로 작성했다.
