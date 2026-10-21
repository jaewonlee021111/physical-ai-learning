# A06 · 오류 수정

대입한 뒤 변수를 사용한다.

## 수정 diff
```diff
--- A06_broken.py
+++ A06_fixed.py
@@ -1,2 +1,2 @@
+count = 3
 print(count)
-count = 3
```

정상·의도한 오류·수정·확장 4종을 실행한다. 실제 stdout/stderr는 evidence/debug-results.json에 보존한다. 정상/오류 입력은 공식 교안의 짧은 실습 예제이며 확장 해답은 새로 작성했다.
