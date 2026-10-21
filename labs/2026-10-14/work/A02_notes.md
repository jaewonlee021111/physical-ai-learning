# A02 · 오류 수정

따옴표의 시작과 끝을 맞춘다.

## 수정 diff
```diff
--- A02_broken.py
+++ A02_fixed.py
@@ -1,2 +1,2 @@
-print("점검 시작)
+print("점검 시작")
 print("S01", 22.5)
```

정상·의도한 오류·수정·확장 4종을 실행한다. 실제 stdout/stderr는 evidence/debug-results.json에 보존한다. 정상/오류 입력은 공식 교안의 짧은 실습 예제이며 확장 해답은 새로 작성했다.
