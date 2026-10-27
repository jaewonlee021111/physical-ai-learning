#pragma once
#include <WebServer.h>
static WebServer controlServer(80);
static const char PAGE[] PROGMEM = R"HTML(
<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Touch LED Lab</title>
<style>body{font:18px system-ui;max-width:650px;margin:3rem auto;padding:1rem;background:#eef1ee;color:#24352d}button{padding:1rem;margin:.5rem}</style>
<h1>터치와 LED</h1><p id="state">연결 중</p><button onclick="led(1)">켜기</button><button onclick="led(0)">끄기</button>
<script>async function led(on){await fetch('/led',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:'on='+on})}async function refresh(){try{const d=await(await fetch('/status')).json();document.getElementById('state').textContent=`터치: ${d.touch} / raw ${d.raw} / LED ${d.led}`}catch(e){document.getElementById('state').textContent=e.message}setTimeout(refresh,300)}refresh()</script></html>
)HTML";

/// <summary>같은 LAN의 STA 또는 인터넷 없는 SoftAP 제어 서버를 연다.</summary>
void setup()
{
    Serial.begin(115200);
    setupTouch();
#if LAB_MODE == 5
    WiFi.mode(WIFI_AP);
    WiFi.softAP(LAB_AP_SSID, LAB_AP_PASSWORD);
    Serial.printf("AP address http://%s (no Internet)\n", WiFi.softAPIP().toString().c_str());
#else
    setupWifi();
#endif
    controlServer.on("/", HTTP_GET, []()
    {
        controlServer.send_P(200, "text/html; charset=utf-8", PAGE);
    });
    controlServer.on("/status", HTTP_GET, []()
    {
        String value = String("{\"touch\":") + (touched ? "true" : "false") + ",\"raw\":" + String(touchRaw) + ",\"led\":" + (ledOn ? "true" : "false") + "}";
        controlServer.send(200, "application/json", value);
    });
    controlServer.on("/led", HTTP_POST, []()
    {
        String value = controlServer.arg("on");
        if (value != "0" && value != "1")
        {
            controlServer.send(400, "text/plain", "on must be 0 or 1");
            return;
        }
        setLed(value == "1");
        controlServer.send(200, "application/json", "{\"ok\":true}");
    });
    controlServer.begin();
}
/// <summary>원격 LED 명령과 터치 변화를 처리한다. 원격 값은 다음 터치 변화까지 유지된다.</summary>
void loop()
{
#if LAB_MODE == 4
    pollWifi();
#endif
    if (pollTouch())
    {
        setLed(touched);
    }
    controlServer.handleClient();
    delay(5);
}
