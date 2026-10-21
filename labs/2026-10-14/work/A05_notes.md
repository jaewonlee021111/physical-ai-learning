# A05 · 오류 수정

계산 결과를 stock에 재대입한다.

## 수정 diff
```diff
--- A05_broken.py
+++ A05_fixed.py
@@ -1,3 +1,3 @@
 stock = 8
-stock + 3
+stock = stock + 3
 print(stock)
```

정상·의도한 오류·수정·확장 4종을 실행한다. 실제 stdout/stderr는 evidence/debug-results.json에 보존한다. 정상/오류 입력은 공식 교안의 짧은 실습 예제이며 확장 해답은 새로 작성했다.
