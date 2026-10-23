# 출처와 작성 기준

- 1차 자료: 사용자가 열람을 요청한 비공개 Zoom 녹화. 페이지 표시 날짜 2026-10-22, 총 길이 07:45:32. 녹화 제목은 피지컬 AI 기초반 직무교육이다.
- 확인 방법: 시작·중간·종료를 포함한 자동 자막의 수업 흐름과 강사가 공유한 채팅의 1~8단계 상세 요구사항·타임스탬프를 대조했다. 전체 영상을 연속 재생하며 시청했다는 의미는 아니다. 자동 자막의 발음·모델명은 강사 채팅과 공식 문서로 보완했다.
- 수업 시간표의 시점은 녹화 상대 시간이다. 각 단계의 모든 코드가 그 시각에 완성됐다는 뜻은 아니다.
- 공개 범위: 직접 쓴 요약·새 예제 코드·직접 생성한 합성 입력·실행 결과. 수강생 이름·채팅, 원본 영상, 접근 암호, 비공개 링크와 다운로드 토큰은 제외한다.
- 코드는 강사가 AI로 만든 파일의 원본 사본이 아니다. 단계별 스크립트가 공통 엔진을 공유하도록 새로 설계했다. 수업의 선택 옵션인 GPU·OpenVINO와 실제 카메라/GUI는 구현 또는 안내가 있어도 실행 완료로 표시하지 않는다.
- 공식 bus 사진은 YOLO 추론용 외부 테스트 입력으로만 사용했다. 공개 저장소에는 사진과 그 사진을 재가공한 이미지 대신 입력 SHA-256과 탐지·시간 JSON을 기록한다. 직접 재현 시 `https://ultralytics.com/images/bus.jpg`를 내려받아 `step6_yolo_image.py --image bus.jpg`로 실행한다.

공식 기술 참고:

- [Ultralytics YOLO26](https://docs.ultralytics.com/models/yolo26/)
- [Ultralytics Predict·Results·speed](https://docs.ultralytics.com/modes/predict/)
- [OpenCV 색 공간](https://opencv.org/color-spaces-in-opencv/)
- [OpenCV 이미지 인코딩](https://docs.opencv.org/4.0.0/d4/da8/group__imgcodecs.html)
- [PlatformIO XIAO ESP32S3 보드 ID](https://docs.platformio.org/en/latest/boards/espressif32/seeed_xiao_esp32s3.html)
- [Tera Term 프로젝트](https://teratermproject.github.io/index-en.html)

Ultralytics와 해당 모델을 다른 프로젝트에 배포·재사용할 때는 원 프로젝트의 라이선스를 확인한다. 이 저장소에 모델 가중치나 라이브러리를 재배포하지 않는다.
