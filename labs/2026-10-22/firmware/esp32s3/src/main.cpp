// 10/22에는 프로젝트 환경 준비. 카메라 핀 설정·원격 전송은 다음 수업 범위.
#include <Arduino.h>

void setup() {
    Serial.begin(115200);
    delay(1500);
    Serial.println("XIAO ESP32S3 project ready");
}

void loop() {
    Serial.println("heartbeat: camera firmware not configured yet");
    delay(1000);
}
