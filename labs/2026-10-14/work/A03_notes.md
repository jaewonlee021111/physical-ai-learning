# A03 · 오류 수정

주석은 실행되지 않는다.

## 수정 diff
```diff
--- A03_broken.py
+++ A03_fixed.py
@@ -1,2 +1,2 @@
 # 아래 줄은 안내를 출력합니다.
-# print("오늘의 점검")
+print("오늘의 점검")
```

정상·의도한 오류·수정·확장 4종을 실행한다. 실제 stdout/stderr는 evidence/debug-results.json에 보존한다. 정상/오류 입력은 공식 교안의 짧은 실습 예제이며 확장 해답은 새로 작성했다.
