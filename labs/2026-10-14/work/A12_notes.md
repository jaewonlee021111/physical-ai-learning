# A12 · 오류 수정

분기 안의 문장은 들여쓴다.

## 수정 diff
```diff
--- A12_broken.py
+++ A12_fixed.py
@@ -1,6 +1,6 @@
 temperature_c = 25.0
 if temperature_c > 24.0:
-print("확인")
+    print("확인")
     print("담당자에게 알림")
 else:
     print("정상")
```

정상·의도한 오류·수정·확장 4종을 실행한다. 실제 stdout/stderr는 evidence/debug-results.json에 보존한다. 정상/오류 입력은 공식 교안의 짧은 실습 예제이며 확장 해답은 새로 작성했다.
