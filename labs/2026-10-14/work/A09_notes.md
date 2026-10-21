# A09 · 오류 수정

덧셈 전체를 괄호로 묶은 뒤 나눈다.

## 수정 diff
```diff
--- A09_broken.py
+++ A09_fixed.py
@@ -1,3 +1,3 @@
 a = 20
 b = 24
-print(a + b / 2)
+print((a + b) / 2)
```

정상·의도한 오류·수정·확장 4종을 실행한다. 실제 stdout/stderr는 evidence/debug-results.json에 보존한다. 정상/오류 입력은 공식 교안의 짧은 실습 예제이며 확장 해답은 새로 작성했다.
