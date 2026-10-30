#pragma once
#define WIFI_SSID "YOUR_2_4GHZ_SSID"
#define WIFI_PASSWORD "YOUR_PASSWORD"
#define MQTT_HOST "YOUR_PC_LAN_IP"
#define MQTT_PORT 1883
#define NODE_ID "xiao"
#define API_BASE "https://YOUR_BACKEND"
#define DEVICE_ID "REGISTER_FROM_DASHBOARD"
#define DEVICE_KEY "ONE_TIME_DEVICE_KEY"
// Paste the actual trusted issuer root CA PEM for your deployment.
// Empty CA makes HTTPS requests fail; certificate checking is never disabled.
#define ROOT_CA ""
