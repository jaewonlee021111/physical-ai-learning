# A13 · 오류 수정

길이 3인 리스트의 마지막 인덱스는 2다.

## 수정 diff
```diff
--- A13_broken.py
+++ A13_fixed.py
@@ -1,3 +1,3 @@
 temperatures = [22.5, 24.0, 23.5]
 print(temperatures[0])
-print(temperatures[3])
+print(temperatures[2])
```

정상·의도한 오류·수정·확장 4종을 실행한다. 실제 stdout/stderr는 evidence/debug-results.json에 보존한다. 정상/오류 입력은 공식 교안의 짧은 실습 예제이며 확장 해답은 새로 작성했다.
