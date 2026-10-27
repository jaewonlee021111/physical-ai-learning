#pragma once
#include <HTTPClient.h>
#include <WiFiClientSecure.h>
#include <time.h>

/// <summary>JSON 문자열에 들어갈 문자를 이스케이프한다.</summary>
static String jsonString(String text)
{
    text.replace("\\", "\\\\");
    text.replace("\"", "\\\"");
    text.replace("\r", "\\r");
    text.replace("\n", "\\n");
    text.replace("\t", "\\t");
    return "\"" + text + "\"";
}

/// <summary>장치 capability key로 허용된 Supabase RPC만 호출한다. 인증서 검증을 끄지 않는다.</summary>
static String rpc(const char *method, String fields = "")
{
    WiFiClientSecure transport;
    transport.setCACert(SUPABASE_CA_PEM);
    HTTPClient http;
    String url = String(SUPABASE_URL) + "/rest/v1/rpc/" + method;
    if (!http.begin(transport, url))
    {
        return "";
    }
    http.setTimeout(3000);
    http.addHeader("apikey", SUPABASE_ANON_KEY);
    http.addHeader("Authorization", String("Bearer ") + SUPABASE_ANON_KEY);
    http.addHeader("Content-Type", "application/json");
    String body = String("{\"p_id\":") + jsonString(DEVICE_ID) + ",\"p_key\":" + jsonString(DEVICE_KEY) + fields + "}";
    int status = http.POST(body);
    String response = status == 200 ? http.getString() : "";
    if (status != 200)
    {
        Serial.printf("Supabase RPC failed: HTTP %d (credentials are not logged)\n", status);
    }
    http.end();
    return response;
}

/// <summary>클라우드 제어를 준비한다. 설정이 없으면 외부 요청을 하지 않는다.</summary>
void setup()
{
    Serial.begin(115200);
    setupTouch();
    setupWifi();
    configTime(0, 0, "pool.ntp.org", "time.cloudflare.com");
}

/// <summary>클라우드 LED 목표값을 읽고 터치 상태를 보고한다. 외부 계정 설정 후에만 동작한다.</summary>
void loop()
{
    pollWifi();
    pollTouch();
    static uint32_t last = 0;
    bool configured = strlen(SUPABASE_URL) > 0 && strlen(DEVICE_KEY) >= 32 && strlen(DEVICE_ID) > 0 && strlen(SUPABASE_ANON_KEY) > 0 && strlen(SUPABASE_CA_PEM) > 0;
    // TLS 인증서 유효 기간을 검증할 수 있는 시각까지 전송하지 않는다.
    bool timeReady = time(nullptr) >= 1704067200;
    if (configured && WiFi.status() == WL_CONNECTED && !timeReady && millis() - last >= 5000)
    {
        last = millis();
        configTime(0, 0, "pool.ntp.org", "time.cloudflare.com");
        Serial.println("Waiting for network time before verified HTTPS. Check NTP access.");
    }
    if (configured && timeReady && WiFi.status() == WL_CONNECTED && millis() - last >= 1000)
    {
        last = millis();
        String response = rpc("lab_read");
        response.replace(" ", "");
        response.replace("\n", "");
        if (response.indexOf("\"desired\":true") >= 0)
        {
            setLed(true);
        }
        else if (response.indexOf("\"desired\":false") >= 0)
        {
            setLed(false);
        }
        rpc("lab_report", String(",\"p_touch\":") + (touched ? "true" : "false") + ",\"p_raw\":" + String(touchRaw));
    }
    if (!configured && millis() - last >= 5000)
    {
        last = millis();
        Serial.println("Cloud not configured: set project URL, anon JWT, device id/key and trusted CA in secrets.h.");
    }
    delay(10);
}
