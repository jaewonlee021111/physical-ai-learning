# 출처와 재구성 범위

확인일: 2026-10-30. 사용자 제공 10/27 Zoom 녹화의 페이지 제목·날짜, 자동 자막 786개 항목, 강사 채팅, FastAPI Swagger 등 일부 공유 화면을 확인했다. 8시간 전체 영상을 연속 시청한 것은 아니다. 제공 자막은 녹화 처음부터 존재하지 않으므로 자막이 없는 도입 구간의 세부 내용까지 확정하지 않는다. 공개 원문 전체·비공개 접속 URL·암호·개인별 채팅은 포함하지 않는다.

강의에서 확인한 주제와 새로 작성한 예제를 README에서 연결했다. 소스는 강사 원본 파일의 동일 복제품이 아니다. SQLite/PostgreSQL 선택 구조, 기기 키·명령 만료·ACK 세부 설계는 복습을 위한 구현 선택이다. 실시간 카메라 프리뷰와 Supabase Auth는 이 버전에 구현하지 않았다. 확인된 이미지 수집과 다음 날 학습·추론의 범위를 분리했다.

구현 시 확인한 공식 문서:

- [FastAPI JWT 인증](https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/): PyJWT·pwdlib·OAuth2 bearer 흐름.
- [FastAPI 여러 파일 구조](https://fastapi.tiangolo.com/tutorial/bigger-applications/): APIRouter·의존성.
- [Seeed XIAO ESP32S3 Wi-Fi/MQTT](https://wiki.seeedstudio.com/xiao_esp32s3_wifi_usage/): WiFi·PubSubClient 연결 예시.
- [Paho Python Client](https://eclipse.dev/paho/files/paho.mqtt.python/html/client.html): callback API와 발행·구독.
- [Supabase PostgreSQL 연결](https://supabase.com/docs/guides/database/connecting-to-postgres): 서버 DB 연결 참고. 실제 DB 접속 검증과는 별개다.

공식 교육 사이트의 공개 날짜 목록에 27일이 없더라도 제공 녹화에서 확인된 보완 내용으로 기록한다. [28일 출처](../2026-10-28/SOURCES.md)와 연결한다.
