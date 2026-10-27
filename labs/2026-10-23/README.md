# 2026-10-23 · ESP32 무선 통신과 원격 카메라

XIAO ESP32S3 Sense로 USB 업로드에서 Wi-Fi·BLE 원격 제어까지 확장하는 수업이다. 제공된 녹화(09:26 시작, 7시간 22분)의 자동 자막과 강사 채팅을 대조해 범위를 확인했다. 자막은 일부 누락·오인식이 있어 공식 문서로 핀과 API를 확인했다. 비공개 녹화 URL·수강생 정보·주변 네트워크 식별자는 저장하지 않았다.

## 오늘 배운 것과 만든 파일

| 수업 흐름 | 구현 | 동작 |
|---|---|---|
| 보드·카메라·안테나 조립, USB/COM 확인 | `firmware/` 공통 설정 | PlatformIO, USB CDC, 시리얼 115200 |
| 주변 Wi-Fi·BLE 검색 | `scanner` | Wi-Fi 채널·RSSI·인증 방식과 BLE 검색 결과 출력 |
| Blink와 정전식 터치 | `blink`, `touch` | 내장 LED 점멸, D0(GPIO1) 터치 보정·디바운싱 |
| STA: 같은 공유기에 접속 | `sta` | 웹에서 LED 제어, 터치 상태 조회 |
| AP: 보드가 직접 네트워크 생성 | `ap` | 인터넷 없이 휴대폰을 보드 Wi-Fi에 연결해 제어 |
| BLE GAP/GATT | `ble`, `web/ble.html` | 장치 광고, LED 쓰기, 터치 읽기·알림 |
| 카메라·PSRAM·웹 스트림 | `camera` | MJPEG, 단일 JPEG, 상태 API |
| ESP32 → PC 비전 대시보드 | `gateway/` | 원격 JPEG 디코딩 → 기존 OpenCV·YOLO·Flask 파이프라인 |
| Supabase 외부 LED 제어 | `cloud`, `cloud/schema.sql`, `web/cloud.html` | 장치별 키를 확인하는 RPC, 명령·센서 상태 교환 |
| Tailscale 외부 영상 접근 | [외부 접속 안내](REMOTE.md) | PC 게이트웨이를 같은 tailnet의 휴대폰에 제공 |

MQTT·Edge AI·라즈베리 파이는 다음 수업 예고였다. 오늘 완료한 실습으로 포함하지 않았다.

## 1. 보드 업로드

대상은 **XIAO ESP32S3 Sense**다. 다른 ESP32 보드에 핀을 그대로 적용하지 않는다. 카메라 확장 보드와 안테나를 연결하고 데이터 전송 가능한 USB 케이블을 사용한다.

```sh
python -m pip install platformio==6.2.0
cd labs/2026-10-23/firmware
python -m platformio device list
python -m platformio run -e blink
python -m platformio run -e blink -t upload --upload-port COM본인포트
python -m platformio device monitor --port COM본인포트 --baud 115200
```

Windows의 COM 번호는 본인 장치 관리자에서 확인한다. macOS/Linux에서는 해당 장치 경로로 바꾼다. 업로드 전 시리얼 모니터를 닫는다. 업로드가 안 되면 케이블·드라이버·점유 프로그램을 확인하고 제조사 BOOT/RESET 절차로 부트로더에 진입한다.

`-e blink`를 `scanner`, `touch`, `sta`, `ap`, `ble`, `camera`, `cloud` 중 하나로 바꾼다. **한 번에 한 펌웨어만 실행**하며 새 업로드는 이전 모드를 대체한다. `touch`는 D0에 도선을 연결하고 전원을 켠 뒤 초기 1초 동안 만지지 않는다. ESP32-S3는 접촉 시 측정값이 증가하며 배선에 따라 보정이 필요하다.

## 2. STA·AP 웹 제어

`firmware/include/secrets.example.h`를 같은 폴더의 `secrets.h`로 복사해 **로컬에서만** 수정한다. 실제 파일은 gitignore에 포함되어 있다.

- STA·camera·cloud: `WIFI_SSID`, `WIFI_PASSWORD`에 본인 2.4 GHz 네트워크를 입력한다. 또는 시리얼에서 `SCAN`, `CONNECT 번호 비밀번호`를 입력한다. PC도 같은 LAN에 연결한다. 클라이언트 격리 설정이 있으면 서로 접속되지 않을 수 있다.
- STA: 시리얼에 출력된 IP의 `http://보드IP/`에서 LED 버튼·터치 상태를 확인한다. `/status`, `POST /led`를 제공한다. 터치 상태가 바뀌면 LED에도 반영되고 원격 명령은 다음 터치 변화 전까지 유지된다.
- AP: `LAB_AP_SSID`·`LAB_AP_PASSWORD`를 변경해 업로드한다. 휴대폰에서 그 Wi-Fi에 연결한 뒤 `http://192.168.4.1/`을 연다. 인터넷 연결 없음 표시는 이 모드에서 정상이다.

## 3. BLE

`ble`을 업로드하고 nRF Connect에서 `PhysicalAI-Touch`를 찾는다. 서비스 UUID는 `34cf0001-5a3b-4ab9-9469-e152c1b37c01`이다. 끝의 첫 묶음이 `0002`인 특성은 터치 읽기·알림, `0003`은 LED 읽기·쓰기·알림이다. 값은 **ASCII 문자 `0` 또는 `1`**이다. 알림을 구독하고 D0를 만져 상태 변화를 확인한다.

브라우저 대안:

```sh
cd labs/2026-10-23/web
python -m http.server 8000 --bind 127.0.0.1
```

지원되는 데스크톱/Android Chrome에서 `http://localhost:8000/ble.html`을 열고 연결 버튼으로 장치를 선택한다. Web Bluetooth는 HTTPS 또는 localhost와 사용자 클릭이 필요하다. iOS 등 미지원 환경에서는 nRF Connect를 사용한다. 웹 페이지를 만들었다고 실제 BLE 연결까지 검증한 것은 아니다.

## 4. 카메라와 PC 영상 처리

`camera`를 업로드하면 VGA JPEG·PSRAM 버퍼 2개를 사용하고, PSRAM이 없으면 QVGA·DRAM 버퍼 1개로 낮춘다. SD 카드는 사용하지 않는다.

| 주소 | 기능 |
|---|---|
| `http://보드IP/` | 안내 링크 |
| `http://보드IP/stream` | 80번 포트 MJPEG |
| `http://보드IP:81/capture` | 단일 JPEG |
| `http://보드IP:81/status` | IP·RSSI·가동시간·PSRAM·해상도·FPS·접속 수 |

펌웨어의 스트림 처리 구조상 보드의 MJPEG는 **게이트웨이 한 개만 구독**한다. 보드 스트림을 연 브라우저는 닫은 뒤 다음 명령을 실행한다.

```sh
python -m pip install -r labs/2026-10-22/vision/requirements.txt
cd labs/2026-10-23/gateway
python server.py --url http://보드IP/stream --no-yolo
# 영상 수신 확인 뒤 실제 추론
python server.py --url http://보드IP/stream --model yolo26n.pt --device cpu
```

`http://127.0.0.1:5050/`에서 대시보드를 연다. YOLO26n을 사용할 수 없는 환경에서는 기존 검출기의 YOLO11n 대체 경로를 사용한다. 모델 다운로드·실제 추론에는 해당 패키지와 모델 파일이 필요하다. 연결이 끊겼을 때 합성 영상으로 성공처럼 표시하지 않는다. 화면 상태는 `remote` 입력을 구분한다. 사진·로그는 gitignore된 `gateway/runtime/`에 저장한다.

## 5. 외부 접속·클라우드

[REMOTE.md](REMOTE.md)에 Tailscale 접속과 Supabase 설정 순서가 있다. 각자 계정·인증 정보가 필요하며 제공된 SQL 파일 자체가 외부 DB를 변경하지는 않는다.

## 검증 상태

[검증 기록](VALIDATION.md)에서 코드 시험과 장비 시험을 구분한다. 펌웨어 8종 컴파일과 Python 통합 시험은 통과했다. 실제 보드 업로드·터치 임계값·카메라 촬영·휴대폰 BLE·본인 Supabase/Tailscale 계정 연결은 사용자 장비에서 확인해야 한다.

[개념·문제 해결](NOTES.md) · [공식 참고 자료](SOURCES.md)
