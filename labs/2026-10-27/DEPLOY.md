# 외부 제어를 위한 설정

강의에서는 Supabase·배포 플랫폼·ESP32를 연결해 외부망 제어를 시연했다. 이 저장소 작업은 배포 가능한 소스와 설정 안내까지이며 사용자의 Supabase DB 생성·접속, Render/Vercel 배포, LTE 제어 시험은 수행하지 않았다.

## 백엔드와 DB

로컬은 SQLite다. Supabase를 사용할 경우 프로젝트가 제공하는 PostgreSQL **직접 연결 또는 session pooler** URL을 서버 환경변수 DATABASE_URL에 입력한다. SQLAlchemy 드라이버 형식은 `postgresql+psycopg://사용자:비밀번호@호스트:포트/postgres?sslmode=require`다. 비밀번호의 특수 문자는 URL 인코딩한다. 실제 URL은 공개 파일에 저장하지 않는다.

앱은 `learning27` 스키마에 학습용 테이블을 만든다. 접속 역할에는 스키마 생성·사용 권한이 필요하다. 기존 public 테이블을 덮어쓰지 않는다. Supabase의 공개 Data API나 브라우저 anon key 경유 CRUD가 아니라 서버 전용 SQL 연결이다. 프로젝트에서 해당 스키마를 Data API exposed schemas에 추가하지 않는다. 이 PostgreSQL 경로는 실제 접속으로 검증하지 않았다.

서버에 32자 이상의 무작위 JWT_SECRET을 설정한다. 별도 웹 출처를 쓰면 CORS_ORIGINS를 정확한 HTTPS origin으로 지정한다. 루트에서 실행할 때 작업 디렉터리는 `labs/2026-10-27`이다. Dockerfile의 컨텍스트도 이 폴더로 설정한다. 실행 명령은 `uvicorn app.main:app --host 0.0.0.0 --port $PORT`, health 경로는 `/health`다. 이 설정은 예시이며 플랫폼 계정이나 유료 리소스를 자동 생성하지 않는다.

같은 서버의 `/web/`을 사용하면 프런트엔드 별도 배포 없이 가능하다. Vercel 같은 정적 호스팅에 `web/`만 올리는 경우 `config.js`의 `window.API_BASE`를 실제 HTTPS 백엔드 origin으로 바꾸고 CORS_ORIGINS에도 프런트엔드 origin을 넣는다. Swagger 링크는 그 백엔드의 `/docs`로 직접 연다. 웹 코드에 DB 비밀번호·JWT 서명 키·기기 키를 고정해서 넣지 않는다.

## 보드 연결

웹 가입·로그인 후 보드를 등록하면 device_key가 한 번 표시된다. 본인 보드의 비밀 설정에 ID와 함께 저장한다. `API_BASE`는 `/api/v1`을 제외한 백엔드 origin이다. HTTPS는 실제 인증기관 ROOT_CA PEM과 NTP 시각이 있어야 연결한다. `setInsecure()`로 우회하지 않는다. 인증서 교체 시 루트 신뢰 설정도 확인한다. 로컬 평문 HTTP는 신뢰하는 LAN 실습에만 쓴다.

`platformio run -e http` 후 보드에서 telemetry POST → next-command GET → 출력 적용 → ACK POST를 반복한다. 웹의 pending 응답만으로 성공 판정하지 않고 같은 명령 ID의 applied와 보드 상태를 확인한다. 미접속 never_seen, 10초 지난 stale, 만료·오류를 각각 시험한다. 실제 서비스화 전에는 부하·접속 복구·비밀 교체·TLS·백업·권한 정책을 추가 검토한다.
