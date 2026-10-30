# MQTT 실습

Mosquitto 설치 후 이 폴더에서 별도 터미널 두 개를 사용한다.

```sh
mosquitto -c mqtt/mosquitto.conf -v
python -m uvicorn mqtt.bridge:app --host 127.0.0.1 --port 8001
```

`http://127.0.0.1:8001/`가 대시보드다. `/docs`에서도 상태와 명령을 시험할 수 있다. 상태 토픽은 `physicalai/xiao/state`, 명령 토픽은 `physicalai/xiao/command`이다.

```json
{"raw": 12345, "touched": false, "led": false, "last_command_id": ""}
```

```json
{"id": "unique-command-id", "led": true}
```

상태는 마지막 수신 후 10초가 지나거나 retained이면 stale이다. 명령 발행 응답은 `published_not_hardware_confirmed`다. 보드가 보내는 상태에서 같은 `last_command_id`와 LED 값을 확인한다.

제공 Mosquitto 설정은 loopback 전용이다. 실제 보드·휴대폰은 같은 신뢰할 수 있는 LAN에 두고 브로커의 LAN 주소에만 listener를 바인딩하도록 별도 설정한다. 인터넷 포트 공개는 이 실습에 필요하지 않다. 펌웨어의 기본 MQTT 연결은 인증 없는 로컬 실습 전용이며 공유 네트워크·인터넷용 TLS/계정 구현은 포함하지 않는다.

## 보드 설정

XIAO ESP32S3 보드와 USB 데이터 케이블을 사용한다. `firmware/include/`를 만들고 `firmware/secrets.example.h`를 `firmware/include/secrets.h`로 복사한다. Wi-Fi와 MQTT_HOST에 실제 로컬 값을 입력한다. NODE_ID는 영문·숫자·밑줄·하이픈으로 정한다. 비밀 설정은 Git에서 제외된다.

```sh
cd firmware
python -m platformio run -e mqtt
python -m platformio run -e mqtt -t upload
python -m platformio device monitor
```

D0(GPIO1)에 터치 입력을 연결하고 부팅 중에는 만지지 않는다. 초기 기준의 1.3배를 터치로 보는 ESP32S3 예시이며 환경별 조정이 필요하다. 내장 LED는 active-low다. HTTP 버전은 `-e http`로 빌드하고 [별도 안내](DEPLOY.md)의 기기 ID·키·HTTPS 인증서를 설정한다. 이번 작업에서 실제 보드 업로드는 수행하지 않았다.
