# 웹캠 → OpenCV → YOLO → Flask

녹화의 8단계를 새 코드로 재구성했다. `step2`, `step3`, `step8`은 공통 웹 엔진을 공유하며, 각 파일을 직접 실행할 수 있다. 강사의 생성 코드를 그대로 복사한 파일은 아니다.

## 설치

Python 3.10 이상. 터미널에서 이 폴더로 이동한다.

```sh
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1
# macOS/Linux에서는 위 줄 대신
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-yolo.txt
```

CPU 전용 PyTorch를 설치할 경우 [공식 설치 선택기](https://pytorch.org/get-started/locally/)를 따른다. torch/torchvision 설치가 끝난 뒤 다음 패키지 설치를 진행한다. 확인 환경은 Python 3.12, OpenCV 5.0.0, Ultralytics 8.4.184, torch 2.14.1+cpu, torchvision 0.29.1+cpu다. `operator torchvision::nms does not exist` 오류는 torch와 torchvision의 CPU/CUDA 조합이 일치하는지 먼저 확인한다.

OpenCV의 GUI 창 실습에는 `opencv-python`을 사용한다. `opencv-python-headless`와 함께 설치하지 않는다. CUDA·MPS·OpenVINO는 이 실행에서 검증하지 않았다.

## 1~8단계 실행

| 단계 | 명령 | 확인할 것 |
| --- | --- | --- |
| 1. 카메라 | `python step1_webcam.py --probe` 후 `python step1_webcam.py` | 실제 해상도·FPS, shape·dtype·BGR, q 종료. Windows는 필요 시 `--dshow` |
| 2. 웹 스트림 | `python step2_server.py --source camera` | `http://127.0.0.1:5050`, `/video_feed`, 한 생산자·최신 프레임 공유 |
| 3. 촬영 | `python step3_capture.py --source camera` | 촬영 버튼, 최근 이미지 목록, `runtime/captures/`의 JPG·JSON |
| 4. 이미지 기초 | `python step4_opencv_basics.py --image runtime/captures/파일명.jpg` | 픽셀·색 순서·회색 변환과 가로 비교 이미지 |
| 5. 전처리 | `python step5_opencv_practice.py` | 1~6 모드, HSV 트랙바, s 저장, q 종료, 이동평균 FPS |
| 6. 사진 탐지 | `python step6_yolo_image.py --image 사진.jpg` | 320/416/640 크기별 시간·박스 표·수동 시각화와 plot 비교 |
| 7. 실시간 탐지 | `python step7_realtime_yolo.py --mode web --source camera` | YOLO 박스·클래스·장치·추론 간격. 창 모드는 `--mode window` |
| 8. 대시보드 | `python step8_pipeline_dashboard.py --source camera` | XML 설명 노드·단계별 평균 ms·SSE·로그 필터·일시정지·테마 |

서버는 `Ctrl+C`, 창은 `q`로 종료한다. 기본 주소는 localhost이며 원격 공개 서버로 배포하는 설정은 포함하지 않는다. 서버에 연결한 브라우저는 **서버 PC의 카메라**를 본다. 방문자 PC의 카메라를 자동으로 여는 구조가 아니다.

```sh
# 장비 없이 앱 실행: 합성 도형이며 YOLO를 실행하지 않는다고 화면에 표시한다.
python step8_pipeline_dashboard.py --source synthetic --no-yolo
# 실제 모델로 합성 입력의 처리 루프 검사. 도형 인식 성능 시험은 아니다.
python step7_realtime_yolo.py --source synthetic --headless --frames 6
# CPU 설정·클래스 필터
python step7_realtime_yolo.py --mode web --imgsz 320 --skip 3 --conf 0.6 --classes person cup
# 모델 호환 문제 비교
python step6_yolo_image.py --image 사진.jpg --model yolo11n.pt
```

CUDA는 `--device cuda:0`이면 기본 imgsz=640·skip=1, CPU는 320·2다. 명시 옵션이 우선한다. CUDA일 때 half 옵션을 적용한다. OpenVINO는 모델을 먼저 export한 뒤 `--openvino`로 해당 폴더를 사용한다. 수업과 달리 공통 Flask 엔진은 완성된 대시보드도 함께 제공하며, `/stream`·`/video_feed`·`/detect_feed`는 같은 최신 출력 스트림이다.

## 구조와 계측

- `camera.py`: 카메라 검색과 자원 해제. 실제 카메라가 실패하면 합성 영상으로 몰래 전환하지 않는다.
- `pipeline.py`: 전처리·YOLO 결과 추출·박스 그리기·JPEG 압축. ndarray 입력은 BGR, RGB 배열은 인코딩 전에 BGR로 되돌린다.
- `stages.py`: `@stage` 레지스트리, XML 설명 파싱, 시작·종료·소요 시간·프레임·입출력 요약의 최대 500개 링버퍼.
- `app.py`: 카메라 한 개를 소유한 생산자, lock/condition, 최신 출력 한 장, 원본 처리 정보와 촬영 이력.
- `/events`: 200ms 간격 SSE. 한 방향 상태 전달이므로 WebSocket 서버가 필요 없다.
- `timings_ms`: OpenCV 전처리, 모델 내부 전처리·추론·후처리(`Results.speed`), 시각화·출력·캡처를 구분한다. 모델 호출 전체 시간은 `model_call_ms`로 따로 남긴다. 중첩 측정값을 모두 더하면 총 지연 시간과 같지 않다.
- 추론을 생략한 프레임은 이전 박스를 재사용하고 `sampled_out=true`와 WARN 로그를 남긴다. 오래된 박스를 새 추론 결과로 오해하면 안 된다.
- `processing_fps`는 처리 시간의 역수, `stream_fps_estimate`는 출력 제한을 반영한 추정치다. 카메라의 실제 수집 FPS·사용자 브라우저의 렌더 FPS와 동일하지 않다.

## 실제 실행과 남은 확인

```sh
python verify.py
python step4_opencv_basics.py --synthetic --out ../evidence/preprocess
```

[단위 검사 15개](../evidence/unit-tests.txt), [실제 HTTP·MJPEG·SSE·촬영 검사](../evidence/http-check.json), [검증 범위](../evidence/validation.json), [실제 YOLO 사진 추론](../evidence/yolo/yolo-benchmark.json)을 저장했다. 단위 테스트의 가짜 탐지기는 경계 검사에만 쓰며, 실제 YOLO 결과와 분리한다.

카메라 하드웨어·GUI 창·GPU·브라우저 화면 조작은 이 환경에서 확인하지 않았다. 사용자 PC에서 위 단계대로 실제 카메라와 장치를 확인해야 한다. 카메라가 안 열리면 USB·OS 카메라 권한·장치 인덱스·Zoom 등 다른 앱의 사용 여부를 확인한다. 다른 앱을 임의로 강제 종료하지 않는다.

촬영 이미지·모델 가중치·런타임 로그는 `.gitignore`로 제외했다. 공개 예시는 직접 생성한 합성 도형이며 수강생의 얼굴·원본 녹화·개인 채팅을 포함하지 않는다.


## 사용자 PC에서 장비 검사

[FINISH_ON_PC.md](../FINISH_ON_PC.md)의 Windows 실행 파일과 `pc_check.py`로 실제 카메라·선택한 보드 업로드·시리얼 응답을 검사할 수 있다. 검사 결과는 로컬 runtime에만 저장하며 자동으로 GitHub에 보내지 않는다.
