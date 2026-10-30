// XIAO ESP32S3 Sense ONLY. Requires the user's exported EI image classifier.
#include <Arduino.h>
#include <WiFi.h>
#include <WebServer.h>
#include <esp_camera.h>
#include <img_converters.h>
#include <vector>
#include "secrets.h"
#include "model_config.h"
#include EI_MODEL_HEADER
#include "edge-impulse-sdk/dsp/image/image.hpp"

#if !defined(EI_CLASSIFIER_SENSOR) || EI_CLASSIFIER_SENSOR != EI_CLASSIFIER_SENSOR_CAMERA
#error "Export an Edge Impulse CAMERA model"
#endif
#if EI_CLASSIFIER_OBJECT_DETECTION == 1
#error "This example supports whole-image classification, not object detection"
#endif

WebServer server(80);
uint8_t *rawRGB = nullptr, *modelRGB = nullptr;
std::vector<uint8_t> lastJpeg;
String latest = "{\"status\":\"waiting\",\"scores\":{}}";
unsigned long lastAttempt = 0, sequence = 0;
bool cameraReady = false;

String quoted(const char *text) {
  String out = "\"";
  while (*text) {
    char c = *text++;
    if (c == '\\' || c == '"') out += '\\';
    if ((unsigned char)c >= 32) out += c;
  }
  return out + "\"";
}

int readPixels(size_t offset, size_t length, float *out) {
  const size_t pixels = EI_CLASSIFIER_INPUT_WIDTH * EI_CLASSIFIER_INPUT_HEIGHT;
  if (offset > pixels || length > pixels - offset) return -1;
  for (size_t i = 0; i < length; ++i) {
    const size_t p = (offset + i) * 3;
    // EI image DSP expects packed RRGGBB pixels represented as floats.
    out[i] = (modelRGB[p] << 16) | (modelRGB[p+1] << 8) | modelRGB[p+2];
  }
  return 0;
}

const char PAGE[] PROGMEM = R"HTML(<!doctype html><html lang="ko"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Edge AI 관측</title>
<style>body{font:18px system-ui;max-width:850px;margin:2rem auto;padding:1rem;background:#f5f7fb;color:#142334}img{max-width:100%;width:480px}pre{white-space:pre-wrap}button{padding:12px}#state{font-weight:bold}</style>
<h1>ESP32 이미지 분류</h1><p>실제 보드 추론 결과 · 시연용 가짜 결과 없음</p>
<p id="state" role="status">연결 확인 중</p><img id="frame" alt="마지막 추론에 사용한 카메라 원본">
<p id="meta"></p><pre id="scores"></pre><button onclick="poll()">다시 확인</button>
<script>let sequence=-1;async function poll(){try{const r=await fetch('/status',{cache:'no-store'});if(!r.ok)throw Error('HTTP '+r.status);const s=await r.json();document.querySelector('#state').textContent=s.status==='ok'?(s.age_ms>5000?'오래된 결과':'추론 수신 중'):'추론 미확인: '+s.status;document.querySelector('#meta').textContent='프레임 '+(s.sequence??'—')+' / 추론 '+(s.inference_ms??'—')+' ms / 결과 나이 '+(s.age_ms??'—')+' ms';document.querySelector('#scores').textContent=s.status==='ok'?Object.entries(s.scores).map(([k,v])=>k+': '+(v*100).toFixed(1)+'%').join('\n'):'현재 분류 결과 없음';if(s.status==='ok'&&sequence!==s.sequence){sequence=s.sequence;document.querySelector('#frame').src='/capture?seq='+sequence;}}catch(e){document.querySelector('#state').textContent='연결 끊김 · 현재 추론 미확인';document.querySelector('#scores').textContent='';document.querySelector('#frame').removeAttribute('src');}}poll();setInterval(poll,1500);</script></html>)HTML";

unsigned long resultAt = 0;
void setup() {
  Serial.begin(115200);
  if (!psramFound()) { Serial.println("PSRAM required"); return; }
  rawRGB = (uint8_t*)ps_malloc(320 * 240 * 3);
  modelRGB = (uint8_t*)ps_malloc(EI_CLASSIFIER_INPUT_WIDTH * EI_CLASSIFIER_INPUT_HEIGHT * 3);
  if (!rawRGB || !modelRGB) { Serial.println("RGB allocation failed"); return; }
  camera_config_t c = {};
  c.pin_pwdn=-1; c.pin_reset=-1; c.pin_xclk=10;
  c.pin_sccb_sda=40; c.pin_sccb_scl=39;
  c.pin_d0=15; c.pin_d1=17; c.pin_d2=18; c.pin_d3=16;
  c.pin_d4=14; c.pin_d5=12; c.pin_d6=11; c.pin_d7=48;
  c.pin_vsync=38; c.pin_href=47; c.pin_pclk=13;
  c.xclk_freq_hz=20000000; c.ledc_timer=LEDC_TIMER_0; c.ledc_channel=LEDC_CHANNEL_0;
  c.pixel_format=PIXFORMAT_JPEG; c.frame_size=FRAMESIZE_QVGA;
  c.jpeg_quality=12; c.fb_count=1; c.fb_location=CAMERA_FB_IN_PSRAM;
  c.grab_mode=CAMERA_GRAB_WHEN_EMPTY;
  if (esp_camera_init(&c) != ESP_OK) { Serial.println("Camera init failed"); return; }
  cameraReady = true;
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  server.on("/", [](){ server.send_P(200,"text/html; charset=utf-8", PAGE); });
  server.on("/status", [](){
    String payload=latest;
    payload.remove(payload.length()-1);
    payload += ",\"age_ms\":" + String(millis()-resultAt) + "}";
    server.sendHeader("Cache-Control","no-store");
    server.send(200,"application/json",payload);
  });
  server.on("/capture", [](){
    if(lastJpeg.empty()) { server.send(503,"text/plain","No inference frame"); return; }
    if (server.hasArg("seq") && server.arg("seq") != String(sequence)) {
      server.send(409,"text/plain","Frame advanced; refresh status"); return;
    }
    server.sendHeader("Cache-Control","no-store");
    server.sendHeader("X-Frame-Sequence", String(sequence));
    server.setContentLength(lastJpeg.size());
    server.send(200,"image/jpeg","");
    server.client().write(lastJpeg.data(),lastJpeg.size());
  });
  server.begin();
}

void loop() {
  if (!cameraReady) { delay(1000); return; }
  server.handleClient();
  static bool printed = false;
  if (WiFi.status()==WL_CONNECTED && !printed) {
    Serial.println(WiFi.localIP()); printed=true;
  }
  if (millis()-lastAttempt < 1000) { delay(1); return; }
  lastAttempt=millis();
  camera_fb_t *fb=esp_camera_fb_get();
  if (!fb) { latest="{\"status\":\"capture_error\",\"scores\":{}}"; return; }
  bool ok = fb->width==320 && fb->height==240 && fb->format==PIXFORMAT_JPEG;
  if (ok) ok=fmt2rgb888(fb->buf,fb->len,fb->format,rawRGB);
  if (ok) lastJpeg.assign(fb->buf,fb->buf+fb->len);
  esp_camera_fb_return(fb);
  if (!ok) { latest="{\"status\":\"decode_error\",\"scores\":{}}"; return; }
  // Training resize mode must match this center crop + interpolation.
  ei::image::processing::crop_and_interpolate_rgb888(rawRGB,320,240,modelRGB,
        EI_CLASSIFIER_INPUT_WIDTH,EI_CLASSIFIER_INPUT_HEIGHT);
  ei::signal_t signal;
  signal.total_length=EI_CLASSIFIER_INPUT_WIDTH * EI_CLASSIFIER_INPUT_HEIGHT;
  signal.get_data=readPixels;
  ei_impulse_result_t result={};
  if (run_classifier(&signal,&result,false)!=EI_IMPULSE_OK) {
    latest="{\"status\":\"inference_error\",\"scores\":{}}"; return;
  }
  ++sequence; resultAt=millis();
  latest="{\"status\":\"ok\",\"sequence\":"+String(sequence)+
         ",\"inference_ms\":"+String(result.timing.classification)+",\"scores\":{";
  for(size_t i=0;i<EI_CLASSIFIER_LABEL_COUNT;++i) {
    if(i) latest+=",";
    latest+=quoted(result.classification[i].label)+":"+String(result.classification[i].value,6);
  }
  latest+="}}";
  Serial.println(latest);
}
