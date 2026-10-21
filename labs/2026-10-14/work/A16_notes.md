# A16 · 오류 수정

실제 키 temperature_c를 사용한다.

## 수정 diff
```diff
--- A16_broken.py
+++ A16_fixed.py
@@ -1,3 +1,3 @@
 record = {"sensor_id": "S01", "temperature_c": 22.5}
 print(record["sensor_id"])
-print(record["temperature"])
+print(record["temperature_c"])
```

정상·의도한 오류·수정·확장 4종을 실행한다. 실제 stdout/stderr는 evidence/debug-results.json에 보존한다. 정상/오류 입력은 공식 교안의 짧은 실습 예제이며 확장 해답은 새로 작성했다.
