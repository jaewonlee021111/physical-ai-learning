# A04 · 오류 수정

변수 이름은 대소문자를 구별한다.

## 수정 diff
```diff
--- A04_broken.py
+++ A04_fixed.py
@@ -1,3 +1,3 @@
 location = "입구"
-print(Location)
+print(location)
 print("location")
```

정상·의도한 오류·수정·확장 4종을 실행한다. 실제 stdout/stderr는 evidence/debug-results.json에 보존한다. 정상/오류 입력은 공식 교안의 짧은 실습 예제이며 확장 해답은 새로 작성했다.
