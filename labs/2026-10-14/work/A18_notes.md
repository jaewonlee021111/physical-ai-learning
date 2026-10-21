# A18 · 오류 수정

총액은 단가 곱하기 수량이다.

## 수정 diff
```diff
--- A18_broken.py
+++ A18_fixed.py
@@ -1,6 +1,6 @@
 price = 2000
 count = 3
-total = price + count
+total = price * count
 if total >= 5000:
     print(total, "무료 배송")
 else:
```

정상·의도한 오류·수정·확장 4종을 실행한다. 실제 stdout/stderr는 evidence/debug-results.json에 보존한다. 정상/오류 입력은 공식 교안의 짧은 실습 예제이며 확장 해답은 새로 작성했다.
