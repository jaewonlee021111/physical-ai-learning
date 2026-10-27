# 두 보드의 작업 공간 준비

녹화 후반에 확인된 보드는 **XIAO ESP32S3 Sense**와 **UNO 호환 보드**다. ESP32 카메라 원격 전송·초음파 센서·LED·부저의 본 실습은 다음 수업 예고이며, 10/22 완료 내용으로 기록하지 않는다.

| 폴더 | 설정 | 포함한 새 예제 |
| --- | --- | --- |
| `esp32s3/` | `seeed_xiao_esp32s3`, Arduino | 시리얼 heartbeat. Sense 카메라 핀 설정은 아직 없음 |
| `uno/` | `uno`, Arduino, 115200 baud | 내장 LED Blink·시리얼 heartbeat |

## PC에서 진행

1. VS Code에서 PlatformIO IDE 설치 후 재시작한다.
2. USB 케이블은 충전 전용이 아닌 데이터 전송 가능한 제품을 사용한다.
3. UNO 호환 보드의 USB 칩이 CH340인지 확인한다. 필요할 때만 제조사의 OS별 서명된 드라이버를 설치한다. ESP32 보드에 같은 드라이버가 무조건 필요한 것은 아니다.
4. PlatformIO에서 각 폴더를 별도로 연다. 실제 보드 모델과 `board` 설정이 일치하는지 확인한다.
5. 빌드 후 실제 장치 포트를 확인하고 업로드한다. 아래 명령은 사용자 PC에서 실행하는 안내다.

```sh
python -m pip install platformio
python -m platformio run -d uno
python -m platformio device list
python -m platformio run -d uno -t upload
python -m platformio device monitor -b 115200
python -m platformio run -d esp32s3
```

UNO 설정에 LCD·RFID·DHT·IRremote·Keypad·SevSeg·RTC 라이브러리 의존성을 넣었다. 이 라이브러리를 사용한 센서 본 실습까지 했다는 의미는 아니다. 펌웨어는 Arduino C++이며 Python은 설치 도구·비전 서버 쪽 언어다.

Tera Term은 Windows 시리얼 터미널이다. macOS/Linux에서는 PlatformIO Device Monitor 등 해당 OS에서 동작하는 도구를 사용한다. 시리얼 통신 자체에는 인터넷 연결이 필요하지 않으며, 보드 펌웨어와 모니터의 baud rate를 맞춘다.

## 실제 검증 범위

이 실행 환경에는 USB 보드가 없다. 업로드·LED 점멸·시리얼 수신을 완료로 표시하지 않는다. 10/27 GitHub Actions에서 UNO·ESP32S3 모두 컴파일에 성공했다. 로컬 환경의 다운로드 제한과 분리하여 원격 검사 결과를 남겼다. 성공 결과·실행 링크·메모리 사용량은 [build-status.json](../evidence/build-status.json)에 있다.

공식 자료: [PlatformIO XIAO ESP32S3](https://docs.platformio.org/en/latest/boards/espressif32/seeed_xiao_esp32s3.html), [PlatformIO UNO](https://docs.platformio.org/en/latest/boards/atmelavr/uno.html), [Tera Term](https://teratermproject.github.io/index-en.html), [WCH CH341 드라이버](https://www.wch-ic.com/downloads/CH341SER_EXE.html).


SevSeg 의존성은 실제 빌드에서 잘못된 소유자 이름을 발견해 공식 등록 이름 `deanisme/SevSeg@3.7.2`로 수정했다. [공식 등록 정보](https://registry.platformio.org/libraries/deanisme/SevSeg)를 대조했다.
