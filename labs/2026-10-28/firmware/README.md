# XIAO ESP32S3 Sense · 이미지 추론과 웹 관측

`edge_camera/`는 사용자가 내보낸 Edge Impulse **이미지 분류** 모델을 연결하는 실제 펌웨어 소스다. 학습 모델을 포함하지 않으며 모델 없이는 빌드되지 않는다. 이 환경에서는 컴파일·실물 시험을 수행하지 않았다.

## 연결

1. XIAO ESP32S3 Sense 카메라 확장 보드·안테나·데이터 USB를 준비한다. 다른 ESP32-CAM 핀에 그대로 적용하지 않는다.
2. 본인 EI 프로젝트에서 Arduino 라이브러리 ZIP을 내보내 Arduino IDE에 설치한다. 카메라 이미지 분류 모델이어야 하며 객체 검출 모델은 거절한다.
3. `model_config.h`의 헤더를 실제 `프로젝트명_inferencing.h`로 바꾼다.
4. `secrets.example.h`를 `secrets.h`로 복사해 본인 2.4GHz Wi-Fi를 로컬에서 입력한다.
5. 보드를 XIAO ESP32S3, PSRAM을 활성화하고 설치한 ESP32 보드 코어·EI SDK 버전을 기록한다. 이 소스는 `pin_sccb_sda/scl` 이름을 사용하는 코어를 전제로 한다.
6. 모델의 학습 resize 방식을 중앙 crop·보간과 맞춘다. 입력 크기는 모델 매크로로 결정한다. 실제 색 순서와 카메라 방향도 시험한다.
7. 컴파일 후 본인 포트로 업로드한다. 실패 시 보드의 BOOT/RESET 절차를 확인한다. 업로드 뒤 실행에 RESET이 필요한 경우를 수업에서 다뤘다.
8. 시리얼 115200에서 IP를 읽고 같은 LAN의 PC에서 `http://보드IP/`를 연다.

## 구현

- QVGA JPEG → RGB888 → 모델 크기로 crop/resize → packed RGB signal → `run_classifier`.
- 프레임 버퍼는 반환하고 RGB 버퍼는 PSRAM에 유지한다.
- `/status`: 상태·프레임 번호·클래스 점수·추론 시간·결과 나이.
- `/capture`: 마지막 추론 원본 JPEG. 요청 프레임 번호가 바뀌면 409로 응답하므로 다시 상태를 읽는다.
- 웹은 실제 결과만 보여주며 연결·촬영·디코딩·추론 실패와 오래된 값을 구별한다. 실제 모델이나 입력이 없을 때 대체 점수를 만들지 않는다.
- HTTP 처리는 단일 loop에서 추론 사이에 수행한다. 추론 중 응답이 지연될 수 있고, 지연이 크면 웹의 5초 표시 기준을 조정하거나 별도 태스크 설계가 필요하다.

## 실물 확인표

| 시험 | 기대 | 상태 |
| --- | --- | --- |
| 모델 라이브러리 포함 빌드 | 실제 타깃 컴파일·메모리 사용 확인 | NOT_RUN |
| 카메라 원본/모델 crop 일치 | 물체·색·방향 확인 | NOT_RUN |
| 콜라·칙촉·배경 입력 | 클래스별 점수와 오분류 기록 | NOT_RUN |
| 다른 조명·거리·배경 | 독립 입력 성능 확인 | NOT_RUN |
| 카메라/네트워크 실패 | 미확인 표시·가짜 결과 없음 | NOT_RUN |

카메라 핀·RGB signal 구성은 [Seeed 공식 예제](https://wiki.seeedstudio.com/tinyml_course_Image_classification_project/)를 참고해 재구성했다. 실제 모델 export에 포함된 라이선스·예제·SDK가 우선이며, 타깃 설정과 프레임 색 순서는 실물에서 검증한다.
