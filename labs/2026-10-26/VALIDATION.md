# 검증 기록 · 2026-10-27

## 실제로 실행한 검사

[전체 빌드·소프트웨어 CI](https://github.com/jaewonlee021111/physical-ai-learning/actions/runs/40504636601)에서 아래 항목 모두 성공했다.

| 항목 | 결과 |
|---|---|
| UNO 컴파일 | check / rgb / lcd / climate / joystick / keypad / piano / ir / sound, 9종 성공 |
| ESP32 컴파일 | 독립 XIAO Sense camera 환경 성공 |
| Python | 12개 검사 성공 |
| 게임 엔진 | Node 5개 검사 성공 |
| 실제 Chromium | Playwright 4개 검사 성공 |

Python은 실제 로컬 HTTP 테스트 서버의 MJPEG 수신 → JPEG 디코딩 → 처리 스레드 → Flask 촬영 파일 제공, 연결 종료·재접속, 최신 프레임 덮어쓰기 카운터, 시간 합산·실행 평균, 로그 커서·링버퍼, XML 파싱 실패, 설정 검증과 경로 탈출 방지를 검사했다. 이 테스트 서버는 ESP32 장비가 아니다.

Chromium은 합성 입력을 명시한 대시보드에서 SVG 6노드·XML 상세·설정 적용·원본 전환·실제 JPEG 파일·로그 일시정지를 검사했다. 별도 게임 페이지에서 두 모드·폭탄·재시작·일시정지와 Web Serial 미지원 안내를 검사했다. 실제 시리얼 장치 권한을 승인하거나 사용자 보드를 연결하지 않았다.

게임 엔진은 ADC 범위·데드존, 착지·점프, 낙하·재시작, 폭탄의 누름 전환, 탄환 충돌과 무적 시간을 검사했다.

## 실제 YOLO 추론

[실제 모델 CI](https://github.com/jaewonlee021111/physical-ai-learning/actions/runs/40505209838)도 성공했다. Ultralytics 8.4.190과 실제 `yolo26n.pt`를 로드하고 표준 `bus.jpg`를 CPU에서 추론했다. CUDA 요청은 CPU 러너에서 경고 후 CPU로 전환됐으며, 워밍업 후 사람 4명·버스 1대 검출 → Detection 변환 → 박스 표시 → 209,443-byte JPEG 출력까지 확인했다. 이는 예제 이미지 시험이며 실제 카메라 추론 속도 시험은 아니다.

[요약 JSON](results/real-yolo-summary.json)에 검출 결과를 남겼다. 단계별 상세 기록은 해당 실행의 `oct26-real-yolo-report` 아티팩트에서 7일간 제공된다. 로컬 재실행은 `vision/requirements-yolo.txt` 설치 후 `vision` 폴더에서 `python ../tests/smoke_yolo.py`다.

## 컴파일 자원

- ESP32 camera: RAM 64,488 / 327,680 bytes, Flash 1,015,586 / 3,342,336 bytes.
- UNO climate: RAM 603 / 2,048 bytes, Flash 12,178 / 32,256 bytes.

이는 정적 빌드 보고서다. 실제 실행 시 최대 메모리·FPS·센서 오차 측정이 아니다. UNO는 atmelavr 5.1.0, ESP32는 espressif32 8.0.0을 고정했다. 라이브러리 버전은 각 platformio.ini에 적었다.

## 재실행

저장소 루트에서:

```sh
python -m pip install -r labs/2026-10-26/vision/requirements.txt
python -m unittest discover -s labs/2026-10-26/tests -p 'test_*.py' -v
node --test labs/2026-10-26/tests/game.test.mjs
cd labs/2026-10-26/tests/ui
npm ci
npx playwright install --with-deps chromium
npm test
```

브라우저 검사는 localhost 5000·8000 포트를 사용하므로 다른 실행 중 서버를 종료한 뒤 시작한다. 실행 중 카메라 영상은 사용하지 않는다.

## 사용자 장비에서 남은 확인

USB 업로드·포트 인식, 카메라 실제 영상과 무선 지연, RGB 극성, LCD 주소·화면, DHT11 측정, 조이스틱 축·버튼·Web Serial, 키패드 커넥터·부저 음, 리모컨·마이크 입력은 물리 장비가 없어 미검증이다. 가짜 장비 로그·센서 값·회로 사진을 만들지 않았다. 본인 장비에서 [UNO 안내](uno/README.md)와 [카메라 안내](vision/README.md)에 따라 확인한다.
