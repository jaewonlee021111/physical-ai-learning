# 본인 계정으로 외부 제어 연결하기

## Tailscale: PC 영상 게이트웨이에 접근

1. ESP32와 PC를 같은 LAN에 연결하고 README의 게이트웨이를 실행한다.
2. PC에서 `http://127.0.0.1:5050/`의 영상 수신부터 확인한다.
3. PC와 휴대폰에 Tailscale을 설치하고 본인 계정의 같은 tailnet에 참여한다. 조직 정책이 있으면 그 정책을 따른다.
4. PC에서 아래 명령을 실행한다. 초기 HTTPS 사용 승인이 안내되면 본인 tailnet 설정에서 진행한다.

```sh
tailscale serve --bg http://127.0.0.1:5050
tailscale serve status
```

5. 출력된 HTTPS 주소를 Tailscale이 켜진 휴대폰에서 연다. PC의 게이트웨이와 보드는 계속 실행되어 있어야 한다.

이는 같은 tailnet의 허용된 장치용 접근이다. 공개 인터넷 게시인 Funnel을 켜는 절차가 아니며 공유기 포트포워딩도 요구하지 않는다. 다른 Serve 설정이 있는 PC에서는 기존 설정을 먼저 확인한다. 카메라 펌웨어에는 인증 기능이 없으므로 보드의 HTTP 포트를 인터넷에 직접 노출하지 않는다.

## Supabase: LED 명령과 터치 상태

1. 본인 Supabase 프로젝트 SQL Editor에서 [cloud/schema.sql](cloud/schema.sql)을 실행한다. `anon`, `authenticated` 역할이 있는 Supabase용 스키마다.
2. 로컬 터미널에서 UUID와 충분히 긴 임의 키를 만든다. 아래 명령은 키를 화면에 출력하므로 공개 화면 공유·로그에 남기지 않는다.

```sh
python -c "import uuid,secrets; print(uuid.uuid4()); print(secrets.token_urlsafe(32))"
```

3. SQL Editor에서 본인의 UUID와 키로 한 장치를 등록한다. 키 원문은 테이블에 저장하지 않고 SHA-256 해시만 저장한다.

```sql
insert into public.lab_devices(id,key_hash)
values ('본인-UUID',extensions.digest('본인-임의키','sha256'));
```

4. `firmware/include/secrets.h`의 `SUPABASE_URL`, `SUPABASE_ANON_KEY`(프로젝트 legacy anon JWT), `DEVICE_ID`, `DEVICE_KEY`를 설정한다. `SUPABASE_CA_PEM`에는 서버 인증서 검증에 필요한 신뢰 루트 CA를 PEM 문자열로 넣는다. 인증서 체인이 바뀌면 갱신한다. 빈 CA로는 실행하지 않으며 TLS 검증을 끄지 않는다.
5. `cloud` 환경을 빌드·업로드한다. Wi-Fi 연결과 RPC 응답 코드를 확인한다. 보드는 NTP로 시간을 동기화한 뒤 인증서를 검증한다. 대기 메시지가 계속되면 NTP 접근도 확인한다. HTTP 오류 시 URL·키·TLS·프로젝트 SQL 설치를 구분해 점검한다.
6. 로컬 HTTP 서버로 `web/cloud.html`을 열고 URL·anon JWT·장치 UUID·장치 키를 입력한다. LED 명령과 터치 보고 시각을 확인한다. 입력값은 브라우저 저장소에 보관하지 않는다.

`service_role`·DB 비밀번호는 브라우저나 펌웨어에 넣지 않는다. anon JWT만으로 전체 장치 테이블에 접근할 수 없도록 테이블 권한을 철회하고, 고정된 search_path의 제한된 RPC가 장치별 키를 확인한다. 장치 키는 LED 제어 권한이므로 공유하지 않는다. 이 구성은 수업용이며 계정 로그인·사용자별 소유권·감사 기록을 갖춘 제품 인증 체계와 다르다.

이 저장소에서는 SQL의 권한·RPC 동작을 별도로 시험하며 실제 사용자 프로젝트와 휴대폰을 연결했다는 뜻은 아니다.
