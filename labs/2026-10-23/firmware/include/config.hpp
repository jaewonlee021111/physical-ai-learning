#pragma once
#if __has_include("secrets.h")
#include "secrets.h"
#else
#include "secrets.example.h"
#endif
#include <Arduino.h>
#include <WiFi.h>

static String wifiName = WIFI_SSID;
static String wifiPassword = WIFI_PASSWORD;
static String serialLine;
static uint32_t reconnectAt = 0;

/// <summary>주변 Wi-Fi를 검색한다. 출력은 로컬 시리얼에만 남긴다.</summary>
static void scanWifi()
{
    int count = WiFi.scanNetworks();
    Serial.println("# / SSID / RSSI dBm / channel / authentication");
    for (int i = 0; i < count; i++)
    {
        Serial.printf("%d / %s / %d / %d / %d\n", i, WiFi.SSID(i).c_str(), WiFi.RSSI(i), WiFi.channel(i), WiFi.encryptionType(i));
    }
    Serial.println("CONNECT <network-number> <password>, or SCAN. Password is never echoed.");
}

/// <summary>선택한 Wi-Fi에 연결하고 성공·실패를 구분해 출력한다.</summary>
static bool connectWifi()
{
    if (wifiName.isEmpty())
    {
        return false;
    }
    WiFi.begin(wifiName.c_str(), wifiPassword.c_str());
    uint32_t start = millis();
    while (WiFi.status() != WL_CONNECTED && millis() - start < 15000)
    {
        delay(100);
    }
    if (WiFi.status() == WL_CONNECTED)
    {
        Serial.printf("CONNECTED IP=%s RSSI=%d\n", WiFi.localIP().toString().c_str(), WiFi.RSSI());
        Serial.printf("STREAM http://%s/stream\n", WiFi.localIP().toString().c_str());
        return true;
    }
    Serial.println("Wi-Fi connection timed out. Check 2.4 GHz, SSID, password and isolation.");
    return false;
}

/// <summary>시리얼 입력으로 네트워크를 고르고 끊어진 연결을 재시도한다.</summary>
static void pollWifi()
{
    while (Serial.available())
    {
        char character = Serial.read();
        if (character == '\n')
        {
            serialLine.trim();
            if (serialLine == "SCAN")
            {
                scanWifi();
            }
            else if (serialLine.startsWith("CONNECT "))
            {
                int split = serialLine.indexOf(' ', 8);
                String number = split < 0 ? serialLine.substring(8) : serialLine.substring(8, split);
                int index = number.toInt();
                bool numeric = !number.isEmpty();
                for (unsigned int i = 0; i < number.length(); i++)
                {
                    numeric = numeric && isDigit(number[i]);
                }
                if (numeric && index >= 0 && index < WiFi.scanComplete())
                {
                    wifiName = WiFi.SSID(index);
                    wifiPassword = split < 0 ? "" : serialLine.substring(split + 1);
                    connectWifi();
                }
                else
                {
                    Serial.println("Invalid network number. Run SCAN first.");
                }
            }
            serialLine = "";
        }
        else if (character != '\r' && serialLine.length() < 256)
        {
            serialLine += character;
        }
    }
    if (!wifiName.isEmpty() && WiFi.status() != WL_CONNECTED && millis() - reconnectAt >= 10000)
    {
        reconnectAt = millis();
        WiFi.reconnect();
    }
}

/// <summary>STA와 절전 설정을 준비하고 초기 접속을 시도한다.</summary>
static void setupWifi()
{
    WiFi.mode(WIFI_STA);
    WiFi.setSleep(false);
    scanWifi();
    connectWifi();
}

static bool ledOn = false;
static bool touched = false;
static uint32_t touchRaw = 0;
static uint32_t touchThreshold = 0;
static bool touchCandidate = false;
static uint32_t touchCandidateSince = 0;

/// <summary>XIAO의 active-low 내장 LED를 논리 상태로 제어한다.</summary>
static void setLed(bool on)
{
    ledOn = on;
    digitalWrite(LED_BUILTIN, on ? LOW : HIGH);
}

/// <summary>D0(GPIO1) 비접촉 기준값을 측정한다. 보정 중에는 만지지 않는다.</summary>
static void setupTouch()
{
    pinMode(LED_BUILTIN, OUTPUT);
    setLed(false);
    uint64_t total = 0;
    Serial.println("Calibrating D0 touch: do not touch for 1 second.");
    for (int i = 0; i < 32; i++)
    {
        total += touchRead(D0);
        delay(30);
    }
    touchThreshold = static_cast<uint32_t>(total / 32 * 1.5);
    Serial.printf("Touch threshold=%lu (ESP32-S3: touched values increase)\n", static_cast<unsigned long>(touchThreshold));
}

/// <summary>50ms 동안 안정된 터치 상태만 반영한다.</summary>
static bool pollTouch()
{
    touchRaw = touchRead(D0);
    bool next = touchRaw > touchThreshold;
    if (next != touchCandidate)
    {
        touchCandidate = next;
        touchCandidateSince = millis();
    }
    if (next != touched && millis() - touchCandidateSince >= 50)
    {
        touched = next;
        return true;
    }
    return false;
}
