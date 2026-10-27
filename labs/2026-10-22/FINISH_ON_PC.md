# 실제 장비에서 마무리하기

저장소 코드·합성 입력·실제 사진 추론·HTTP 검사는 원격에서 실행할 수 있다. 사용자 PC의 카메라 영상과 USB 보드에는 이 연결로 접근할 수 없으므로 다음 검사는 해당 PC에서 실행해야 한다. 실행 전에는 완료 상태로 표시하지 않는다.

## Windows 카메라와 웹 대시보드

저장소를 내려받은 뒤 `labs/2026-10-22/vision/START_WINDOWS.cmd`를 실행한다. Python이 설치되어 있어야 한다. 필요한 패키지·YOLO 모델 다운로드에는 시간이 걸릴 수 있다. 설치 후 카메라 0번을 실제로 읽고 추론한 다음 대시보드 서버를 연다. 실패 시 오류를 표시하고 중단한다.

카메라 번호가 다른 경우에는 터미널에서 다음처럼 진행한다.

```powershell
cd labs/2026-10-22/vision
.venv\Scripts\python.exe step1_webcam.py --probe
.venv\Scripts\python.exe pc_check.py --camera 1 --yolo
.venv\Scripts\python.exe step8_pipeline_dashboard.py --source camera --camera 1
```

Zoom에서 같은 카메라를 사용 중이면 사용을 끄거나 다른 카메라를 선택한다. 앱은 Zoom을 강제로 종료하지 않는다. 브라우저에서 `http://127.0.0.1:5050`을 연 뒤 원본 영상·촬영·저장 이미지·전처리 선택·탐지 박스·노드 설명·로그 필터·일시정지·테마를 확인한다.

GUI 실습은 `step1_webcam.py`, `step5_opencv_practice.py`, `step7_realtime_yolo.py --mode window`를 실행한다. STEP 5는 1~6 모드·HSV 트랙바·s 저장·q 종료를 확인한다. GUI가 켜졌다는 사실만으로 사람이 모든 조작을 검수했다고 자동 표시하지 않는다.

## UNO와 XIAO ESP32S3

```powershell
.venv\Scripts\python.exe -m platformio device list
.venv\Scripts\python.exe pc_check.py --board uno
.venv\Scripts\python.exe pc_check.py --board esp32s3
```

업로드는 실제 보드와 포트를 확인한 뒤 실행한다. 아래의 COM4/COM5는 예시이므로 실제 값으로 바꾼다. 선택한 보드에는 이 저장소의 최소 확인 펌웨어가 기록된다.

```powershell
.venv\Scripts\python.exe pc_check.py --board uno --port COM4
.venv\Scripts\python.exe pc_check.py --board esp32s3 --port COM5
```

검사 도구는 빌드 → 명시한 포트 업로드 → 115200 baud 시리얼에서 heartbeat 수신을 구분해 기록한다. 임의의 포트를 추측해서 업로드하지 않는다. UNO에서는 내장 LED가 0.5초 간격으로 켜지고 꺼지는지도 직접 확인한다. XIAO의 카메라 원격 전송은 다음 수업 범위이며 이 최소 확인 펌웨어에 포함하지 않았다.

## 검사 결과

가장 최근 검사 결과는 `vision/runtime/pc-check.json`에 저장된다. 얼굴 사진을 자동 저장하거나 GitHub에 자동 전송하지 않는다. `runtime`은 Git에서 제외되어 있다. 개별 명령을 다시 실행하면 이 파일은 가장 최근 검사 결과로 바뀐다.

현재는 이 PC 검사 도구 자체의 예외 처리·카메라 API 호출을 가짜 장치로 단위 검사했다. 이는 사용자 장비 검증 결과와 별개다.
