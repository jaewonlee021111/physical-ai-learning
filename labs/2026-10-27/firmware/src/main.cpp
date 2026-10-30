#include <Arduino.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <HTTPClient.h>
#include <WiFiClientSecure.h>
#include <time.h>
#if __has_include("secrets.h")
#include "secrets.h"
#else
// Compilation defaults contain no real account/device information.
#define WIFI_SSID "CONFIGURE_WIFI"
#define WIFI_PASSWORD "CONFIGURE_WIFI"
#define MQTT_HOST "192.0.2.1"
#define MQTT_PORT 1883
#define NODE_ID "xiao"
#define API_BASE "http://192.0.2.1:8000"
#define DEVICE_ID "CONFIGURE_DEVICE"
#define DEVICE_KEY "CONFIGURE_KEY"
#define ROOT_CA ""
#endif

WiFiClient plain;
WiFiClientSecure secure;
PubSubClient broker(plain);
uint32_t baseline=0;
bool led=false;
String lastCommand="";
unsigned long lastSample=0,lastConnect=0;

void applyLed(bool value) {
  led=value;
  digitalWrite(LED_BUILTIN,led?LOW:HIGH); // XIAO builtin LED is active-low
}

void onMessage(char *topic,byte *payload,unsigned int length) {
  JsonDocument doc;
  if(deserializeJson(doc,payload,length) || !doc["id"].is<const char*>() || !doc["led"].is<bool>()) return;
  String id=doc["id"].as<String>();
  if(id!=lastCommand) { applyLed(doc["led"]); lastCommand=id; }
}

int request(const String &path,const String &body,String &response) {
  HTTPClient http;
  String url=String(API_BASE)+path;
  if(url.startsWith("https://")) {
    if(strlen(ROOT_CA)==0 || time(nullptr)<1700000000) return -1;
    secure.setCACert(ROOT_CA);
    if(!http.begin(secure,url)) return -1;
  } else if(!http.begin(plain,url)) return -1;
  http.setTimeout(5000);
  http.addHeader("X-Device-Key",DEVICE_KEY);
  http.addHeader("Content-Type","application/json");
  int status=body.length()?http.POST(body):http.GET();
  response=http.getString();
  http.end();
  return status;
}

void setup() {
  Serial.begin(115200);
  pinMode(LED_BUILTIN,OUTPUT);
  applyLed(false);
  uint64_t total=0;
  for(int i=0;i<32;i++) {total+=touchRead(1);delay(20);}
  baseline=(uint32_t)(total/32); // Keep D0 untouched during boot.
  WiFi.begin(WIFI_SSID,WIFI_PASSWORD);
  configTime(0,0,"pool.ntp.org");
  broker.setServer(MQTT_HOST,MQTT_PORT);
  broker.setCallback(onMessage);
  broker.setBufferSize(1024);
}

void loop() {
  if(WiFi.status()!=WL_CONNECTED) {delay(20);return;}
#ifdef TRANSPORT_MQTT
  if(!broker.connected() && millis()-lastConnect>5000) {
    lastConnect=millis();
    String clientId=String(NODE_ID)+String((uint32_t)ESP.getEfuseMac(),HEX);
    if(broker.connect(clientId.c_str())) broker.subscribe((String("physicalai/")+NODE_ID+"/command").c_str(),1);
  }
  broker.loop();
#endif
  if(millis()-lastSample<1000) {delay(1);return;}
  lastSample=millis();
  uint32_t raw=touchRead(1);
  JsonDocument data;
  data["raw"]=(uint32_t)min(raw,(uint32_t)2147483647);
  data["touched"]=baseline>0 && (uint64_t)raw*10>(uint64_t)baseline*13;
  data["led"]=led;
  data["last_command_id"]=lastCommand;
  String payload;serializeJson(data,payload);
#ifdef TRANSPORT_MQTT
  broker.publish((String("physicalai/")+NODE_ID+"/state").c_str(),payload.c_str(),false);
#else
  // API schema deliberately excludes MQTT-only last_command_id.
  data.remove("last_command_id");payload="";serializeJson(data,payload);
  String response;
  String prefix=String("/api/v1/device/")+DEVICE_ID;
  request(prefix+"/telemetry",payload,response);
  if(request(prefix+"/next-command","",response)==200) {
    JsonDocument doc;
    if(!deserializeJson(doc,response) && doc["command"]["id"].is<const char*>()) {
      String id=doc["command"]["id"].as<String>();
      if(id!=lastCommand) { applyLed(doc["command"]["led"].as<int>()!=0);lastCommand=id; }
      request(prefix+"/ack/"+id,"{}",response);
    }
  }
#endif
}
