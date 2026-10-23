// 00_check: 내장 LED와 시리얼 출력으로 업로드 환경을 확인하는 새 예제.
#include <Arduino.h>

void setup() {
    pinMode(LED_BUILTIN, OUTPUT);
    Serial.begin(115200);
    Serial.println(F("UNO environment ready"));
}

void loop() {
    digitalWrite(LED_BUILTIN, HIGH);
    delay(500);
    digitalWrite(LED_BUILTIN, LOW);
    delay(500);
    Serial.println(F("heartbeat"));
}
