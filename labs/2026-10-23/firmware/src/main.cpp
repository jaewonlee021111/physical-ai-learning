#include <Arduino.h>
#include "config.hpp"

#if LAB_MODE == 1
#include "scanner.hpp"
#elif LAB_MODE == 2
/// <summary>LED 출력을 준비한다.</summary>
void setup()
{
    pinMode(LED_BUILTIN, OUTPUT);
}
/// <summary>100ms마다 LED를 반전한다. 한 주기는 200ms다.</summary>
void loop()
{
    setLed(!ledOn);
    delay(100);
}
#elif LAB_MODE == 3
/// <summary>터치 입력과 LED를 준비한다.</summary>
void setup()
{
    Serial.begin(115200);
    setupTouch();
}
/// <summary>터치 중에 LED를 켜고 놓으면 끈다.</summary>
void loop()
{
    pollTouch();
    setLed(touched);
    delay(10);
}
#elif LAB_MODE == 4 || LAB_MODE == 5
#include "control.hpp"
#elif LAB_MODE == 6
#include "ble.hpp"
#elif LAB_MODE == 7
#include "camera.hpp"
#elif LAB_MODE == 8
#include "cloud.hpp"
#else
#error Select a lab environment.
#endif
