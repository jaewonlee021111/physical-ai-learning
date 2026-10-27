# 수업 근거와 공식 자료

근거는 사용자가 제공한 **2026-10-26 Zoom 녹화**다. 재생 화면의 날짜·전체 길이, 시작·중간·마무리 자막, 강사 채팅의 P0~P11과 오후 실습 명령을 확인했다. 7시간 전체 영상을 연속 시청한 것은 아니며 자막의 오인식·누락 가능성이 있다. 원본 비공개 링크·암호·자막·학생 이름은 커밋하지 않는다.

- [수업 키트 안내](https://zeusk302-png.github.io/kdigital-physical-ai/downloads/2026-10-23/studio/kit/guide/index.html?lab=K13&step=10#workbench): 조이스틱 핀·빵판 연결 원리. URL 날짜와 녹화 날짜를 구분한다.
- [Seeed 카메라 사용](https://wiki.seeedstudio.com/xiao_esp32s3_camera_usage/): XIAO Sense 핀·PSRAM·JPEG. 10/23 구현 때 확인한 근거를 재사용했다.
- [Ultralytics Predict](https://docs.ultralytics.com/modes/predict/): predict 설정·Results.speed 시간 구분.
- [Arduino-IRremote](https://github.com/Arduino-IRremote/Arduino-IRremote): 수신·결과·resume API. 설치 버전은 4.4.1로 고정하고 컴파일로 확인했다.
- [Adafruit DHT](https://github.com/adafruit/DHT-sensor-library): DHT11 라이브러리·의존성.
- [LiquidCrystal I2C](https://github.com/johnrickman/LiquidCrystal_I2C): LCD init·주소·커서 API.

별도 원본 코드·도형 게임으로 작성했으며 강사 채팅 문장 전체나 타인 코드 묶음을 재배포하지 않는다. 라이브러리는 PlatformIO 의존성으로 설치하고 해당 라이선스를 따른다.
