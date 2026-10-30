# 10/27 · MQTT에서 인증 백엔드와 이미지 수집까지

사용자 제공 녹화의 자동 자막·강사 채팅·일부 공유 화면을 확인해 주제별로 재구성했다. 강사 원본 소스를 복사한 것이 아니라 같은 학습 목표를 실행 가능한 예제로 구현했다. [개념 정리](NOTES.md) · [출처](SOURCES.md) · [실행 검증](VALIDATION.md)

| 강의 주제 | 구현 파일 | 확인 범위 |
| --- | --- | --- |
| MQTT 센서·LED·웹 대시보드 | [브리지](mqtt/bridge.py), [브로커 설정](mqtt/mosquitto.conf), [연결 안내](MQTT.md) | 실제 로컬 TCP 브로커 왕복 시험, ESP32 실물 미연결 |
| 백엔드 용어·퀴즈·오답노트 | [학습 페이지](web/learning.html) | 정적 페이지 소스, 브라우저 조작 검증 미수행 |
| SQLite CRUD·라우터 분리 | [API](app/main.py), [라우터](app/routers/items.py), [DB](app/services/database.py) | 생성·조회·교체·수정·삭제·재시작 후 저장 시험 |
| JWT 로그인·소유권 | [인증](app/routers/auth.py), [의존성](app/deps.py) | 만료·변조·타인 수정·잘못된 입력 거부 시험 |
| 보드 원격 제어·ACK | [보드 API](app/routers/devices.py), [웹 화면](web/index.html), [펌웨어](firmware/src/main.cpp) | 소프트웨어 시험, 물리 LED 및 외부망 시험 미수행 |
| Supabase·배포 구조 | [배포 안내](DEPLOY.md), [Dockerfile](Dockerfile) | 설정과 코드 제공, DB 접속·클라우드 배포 미수행 |
| 클래스별 이미지 수집 | [수집 서버](collector.py), [화면](web/collector.html), [안내](IMAGE-COLLECTION.md) | 로컬 HTTP JPEG 수집·삭제·ZIP 시험 |
| 팀 하드웨어 과제 | [팀 과제 메모](TEAM.md) | 녹화에서 확인한 공통 안내 정리 |

## 실행

이 폴더에서 Python 3.12 가상환경을 만들고 설치한다.

```sh
python -m venv .venv
# macOS/Linux
source .venv/bin/activate
# Windows PowerShell은 .venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

브라우저에서 `http://127.0.0.1:8000/web/`를 연다. 가입(비밀번호 10자 이상) → 로그인 → 아이템 생성·조회·수정·삭제 → 보드 등록 → 명령 요청 순으로 실습한다. Swagger는 `/docs`, 학습 페이지는 `/web/learning.html`이다. 보드가 접속하지 않으면 `never_seen`, 명령은 `pending`으로 남는다. 성공한 것처럼 가짜 센서값을 만들지 않는다.

기본 SQLite는 `runtime/learning.db`에 저장된다. `JWT_SECRET`을 설정하지 않은 로컬 실행은 매번 임시 키를 생성하므로 서버 재시작 후 기존 토큰은 무효다. `.env.example`은 설정 예시이며 자동으로 읽지 않는다. 환경변수는 셸이나 배포 플랫폼에서 직접 설정한다.

## 검사

```sh
python -m pip install -r requirements-test.txt
python -m pytest tests -q
```

12개 통과. MQTT 검사는 AMQTT가 없으면 건너뛰므로 전체 재현에는 `requirements-test.txt`를 설치한다. [검증 기록](evidence/validation.json)에 실제 실행과 미수행을 구분했다. 펌웨어는 설정용 소스를 제공하며 이번 환경에서 빌드·업로드 성공으로 표시하지 않는다.

## 다음 수업과 연결

27일에 카메라 사진을 클래스별로 모으기 시작했다. Edge Impulse의 데이터 분리·학습·평가·모델 배포와 보드 추론은 [28일 실습](../2026-10-28/README.md)으로 이어진다. 27일 수집 기능만으로 모델 학습 완료라고 해석하지 않는다.
