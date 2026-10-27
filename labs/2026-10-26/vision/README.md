# ESP32 → Python → 계측 대시보드

## 1. ESP32 카메라

대상은 XIAO ESP32S3 Sense다. 카메라 리본·확장 보드·안테나를 제조사 지침대로 연결한다. 네이티브 USB 보드이므로 UNO 호환 보드의 CH340 안내를 그대로 적용하지 않는다.

`../esp32/src/wifi_config.example.h`를 같은 폴더의 `wifi_config.h`로 복사하고 본인 **2.4 GHz** Wi-Fi 이름·비밀번호를 로컬에서 설정한다. 실제 설정 파일은 gitignore에 포함했다. 또는 시리얼 `SCAN`, `CONNECT 번호 비밀번호`로 접속한다. 비밀번호를 공개 로그에 올리지 않는다.

저장소 루트에서:

```sh
python -m platformio run -d labs/2026-10-26/esp32 -e camera
python -m platformio run -d labs/2026-10-26/esp32 -e camera -t upload --upload-port COM본인포트
python -m platformio device monitor --port COM본인포트 --baud 115200
```

업로드 실패 시 포트 점유·케이블·장치 인식부터 확인한다. 필요하면 제조사의 BOOT를 누른 채 USB 연결 → 다운로드 모드 → 업로드 → RESET 절차를 따른다. 카메라 초기화 실패는 에러 코드 후 5초 뒤 재시도한다. VGA/JPEG 품질 12·PSRAM 버퍼 2개가 기본이며 PSRAM이 없으면 QVGA·DRAM 1개로 낮춘다. SD 카드는 사용하지 않는다. 프레임은 전송 성공·실패 모두 반환한다.

| URL | 역할 |
|---|---|
| `http://보드IP/` | 임베드 없는 안내 |
| `http://보드IP/stream` | 80번 포트 MJPEG |
| `http://보드IP:81/status` | IP·RSSI·PSRAM·FPS·클라이언트 수 |
| `http://보드IP:81/capture` | 단일 JPEG |

서버 제어 포트도 다르게 설정했다. **보드 스트림은 PC 게이트웨이 한 개만 구독한다.** 보드 영상을 직접 연 브라우저는 닫고 Python을 실행한다. 여러 브라우저는 Python의 공유 출력에 접속한다. 시리얼의 통계는 실제 실행 때 측정되며 이 저장소에 임의 FPS 결과를 넣지 않았다.

## 2. PC 실행

```sh
python -m pip install -r labs/2026-10-26/vision/requirements.txt
cd labs/2026-10-26/vision
# 영상 전송·디코딩 먼저 확인
python step8_pipeline_dashboard.py --source esp32 --url http://보드IP/stream --no-yolo
```

`http://127.0.0.1:5000/`을 연다. 모델을 사용할 때는 같은 폴더에서:

```sh
python -m pip install -r requirements-yolo.txt
# CPU
python step8_pipeline_dashboard.py --source esp32 --url http://보드IP/stream --device cpu --imgsz 320 --skip 2
# CUDA가 준비된 PC. 미지원이면 경고와 함께 CPU로 전환
python step8_pipeline_dashboard.py --source esp32 --url http://보드IP/stream --device cuda:0 --imgsz 320
# USB 웹캠 예비 입력. ESP32 실패 시 몰래 대체하지 않고 직접 선택한다.
python step8_pipeline_dashboard.py --source webcam --webcam-index 0 --no-yolo
# 장비 없는 자동화 검사용. 실제 카메라가 아님을 화면에 명시한다.
python step8_pipeline_dashboard.py --source synthetic --no-yolo
```

YOLO26n 로드가 실패하면 YOLO11n을 시도한다. 둘 다 실패하면 모델 없는 성공 화면으로 위장하지 않고 시작 오류를 낸다. 모델 다운로드와 패키지 설치에는 네트워크가 필요하다. `--classes person car`로 클래스 이름을 제한할 수 있다. `--host`는 기본 localhost다. 카메라·캡처를 외부 공개하는 설정은 포함하지 않는다.

## 3. 어디서 시간이 쓰이는가

- `capture`: 최신 입력 대기·JPEG 디코딩. 수신은 별도 스레드가 하며 큐는 최신 한 장이다. 소비 전 덮어쓴 입력은 dropped로 센다.
- `preprocess`: BGR uint8·최대 폭 정리. 모델 내부 전처리 시간도 이 단계에 합산한다.
- `inference`: 지정 간격으로 모델 실행. `--no-yolo`는 항상 생략한다. YOLO `Results.speed`의 세 단계 시간을 분리해 기록한다.
- `postprocess`: 모델 후처리와 Detection 목록 변환. 생략한 프레임은 직전 결과를 재사용하고 화면에 CACHED로 표시한다.
- `visualize`: 원본을 복사해 박스·라벨·FPS를 그린다.
- `output`: 원본·가공 영상을 JPEG로 한 번씩 인코딩하고 모든 시청자가 공유한다.

단계 평균은 최근 30프레임 기준이다. 추론 생략 프레임을 포함한 평균과 **실제로 실행된 경우의 평균**을 나눠 보여 준다. 처리 FPS·수신 FPS·kbps·PC에서의 프레임 나이를 구분한다. 이 나이는 PC 수신 후 경과이며 ESP32 촬영부터 휴대폰 표시까지의 전체 지연을 의미하지 않는다.

상태는 RLock으로 보호하고 로그는 500개 링버퍼다. INFO·DEBUG와 반복 skip 경고는 기본 5프레임마다 기록하고 다른 경고는 즉시 기록한다. SSE 연결별 커서로 로그를 보내므로 이전 로그가 매 갱신마다 중복되지 않는다. 브라우저 로그는 400줄을 유지하며 일시정지·재개·레벨 필터를 제공한다. 주석 XML이 잘못되면 해당 노드의 오류와 서버 경고를 남긴다.

## 4. HTTP 기능

`GET /`, `/detect_feed`, `/raw_feed`, `/api/pipeline`, `/api/config`, `/events`, `/api/captures`, `/captures/파일`과 `POST /api/settings`, `/capture`를 제공한다. 설정은 skip 1~30 정수, imgsz 160~1280의 32배수, conf 0~1 유한수를 검사한다. 촬영 파일은 지정 폴더 내부에서만 제공한다. 촬영 폴더는 `CAPTURE_DIR` 환경변수로 바꾸며 기본 `runtime/captures`다.

대시보드 흐름은 외부 CDN 없이 SVG로 한 번 만들고 수치만 갱신한다. 노드 클릭 시 실제 함수의 한국어 XML 주석과 실행 평균이 표시된다.
