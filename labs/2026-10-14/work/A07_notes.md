# A07 · 오류 수정

문자열 연결과 숫자 덧셈의 타입을 맞춘다.

## 수정 diff
```diff
--- A07_broken.py
+++ A07_fixed.py
@@ -1,4 +1,4 @@
 count = 3
 text_count = "3"
 print(count + 2)
-print(text_count + 2)
+print(text_count + "2")
```

정상·의도한 오류·수정·확장 4종을 실행한다. 실제 stdout/stderr는 evidence/debug-results.json에 보존한다. 정상/오류 입력은 공식 교안의 짧은 실습 예제이며 확장 해답은 새로 작성했다.
