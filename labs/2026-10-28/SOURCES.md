# 출처·확인 범위·재구성 기준

확인일: 2026-10-30. 원본은 사용자가 제공한 10월 28일 09:05 시작 Zoom 녹화(7시간 45분 53초)다. 공유 링크·암호·전체 자막·수강생 채팅은 공개하지 않는다.

## 확인한 자료

- 재생 페이지의 자동 자막 829개 항목에서 이미지 학습·오분류/추가 수집·프로젝트·아이디어·Git·협업·라즈베리파이 설정을 확인했다.
- 강사 채팅에서 EI 키를 로컬 환경변수로 사용하는 학습 요청, 추론 펌웨어와 로컬 대시보드 요구, 업로드·RESET 안내, 전원·SSH 안내를 대조했다.
- Edge Impulse Impulse Design 공유 화면을 확인했다. 전체 영상을 실시간으로 모두 시청하거나 모든 설정 화면을 OCR로 검증한 것은 아니다. 첫 자막이 시작부부터 제공되지 않고 오인식·수업 중 긴 실습 대기가 있다.
- MobileNet 명칭·epoch·learning rate 등 자막의 불명확한 수치를 확정 설정으로 복제하지 않았다. 실제 exported model metadata가 필요하다.

## 공식 문서 대조

- [Edge Impulse 이미지 전이학습](https://docs.edgeimpulse.com/studio/projects/learning-blocks/blocks/transfer-learning-images)
- [Seeed XIAO ESP32S3 Sense 이미지 분류 예제](https://wiki.seeedstudio.com/tinyml_course_Image_classification_project/): 카메라 핀·RGB 처리·signal callback·run_classifier 참고.
- [Keras MobileNet](https://keras.io/api/applications/mobilenet/mobilenet_models/): alpha 폭 계수와 양자화 개념 구별.
- [Raspberry Pi 공식 시작 문서](https://www.raspberrypi.com/documentation/computers/getting-started.html): Pi 5 전원·5GHz Wi-Fi·SSH/Imager 설명 정정.

실습 코드는 위 원리를 참고해 새로 구성했다. 강사의 원본 프로그램이나 모델 가중치를 확보한 복사본이 아니다. Seeed 전체 예제를 통째로 복사하지 않았고 사용자가 export하는 모델 라이브러리는 원래 라이선스를 유지해야 한다.

## 실제 수행과 제한

Python 도구·자동 검사·임시 Git 협업 재현은 실행했다. [검증 JSON](evidence/validation.json)을 따른다. 테스트의 생성 이미지와 계산용 점수는 실제 물체 사진·모델 평가 증거가 아니다. 강의에서 언급한 모델 성능을 내 모델 결과로 사용하지 않았다.

실제 사진·Edge Impulse 프로젝트 키·exported model이 제공되지 않아 클라우드 학습과 모델 포함 컴파일은 미수행이다. ESP32·라즈베리파이가 연결되지 않아 업로드·촬영·추론·SSH·Connect 역시 미수행이다. 이를 가짜 모델·가짜 장치 응답으로 완료 처리하지 않았다.

취미 PR #2는 GitHub API에서 병합 상태와 병합일만 확인했다. 웹사이트의 현재 배포 화면을 이번 작업에서 별도로 검사하지 않았다.
