# 실행과 미확인 범위

2026-10-30 Python 3.12에서 `python -m pytest tests -q` 실행 결과 **12 passed, 1 warning**이다. Starlette TestClient의 httpx 관련 deprecation 경고가 있었고 실패는 없었다.

| 검사 | 실제 수행 |
| --- | --- |
| CRUD·입력 검사 | 전체 메서드, 잘못된 가격·null·추가 필드, 문자열 SQL 주입 시도 처리 |
| JWT·소유권 | 만료·변조·잘못된 로그인, 타인 자원 변경 거부 |
| DB 영속성 | 새 앱 인스턴스로 SQLite 다시 열어 기존 데이터 확인 |
| 기기 명령 | 개별 키, 소유권, 대기·만료·중복 ACK, 상태 stale |
| 이미지 | 로컬 HTTP 서버가 생성한 JPEG를 실제 요청해 저장·조회·ZIP·삭제 |
| MQTT | AMQTT 로컬 TCP 브로커 + Paho 보드 모사 클라이언트로 상태·명령·응답 왕복 |
| 웹 | 정적 파일 제공 검사. 실제 브라우저 클릭·화면 검수는 미수행 |

FastAPI 검사는 ASGI TestClient로 실행했다. MQTT와 카메라 검사는 로컬 TCP/HTTP 통신을 포함하지만 실제 ESP32나 실제 촬영 장면은 아니다. Mosquitto 설정을 제공했으나 이번 프로토콜 검사는 Mosquitto 대신 AMQTT에서 실행했다.

ESP32 PlatformIO 빌드를 시도했으나 플랫폼 도구 설치/준비 단계에서 컴파일 완료 결과를 얻지 못했다. 펌웨어는 **미빌드 소스**다. 보드 업로드·터치 임계값 조정·물리 LED·실제 카메라·Supabase PostgreSQL·Docker 이미지 빌드·Render/Vercel·휴대폰 외부망 제어·Edge Impulse 학습은 이번 작업에서 수행하지 않았다.

[기계 판독 기록](evidence/validation.json)과 [검사 코드](tests/test_api.py)를 함께 제공한다. 재현 시 `requirements-test.txt`를 설치해야 MQTT 검사 건너뛰기를 피할 수 있다.
