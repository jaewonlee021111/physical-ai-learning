#pragma once
#include <BLEDevice.h>
#include <BLEScan.h>

/// <summary>주변 네트워크 검색을 준비한다.</summary>
void setup()
{
    Serial.begin(115200);
    WiFi.mode(WIFI_STA);
    BLEDevice::init("PhysicalAI-Scanner");
    BLEDevice::getScan()->setActiveScan(false);
}
/// <summary>Wi-Fi와 BLE를 순서대로 검색하고 결과 버퍼를 해제한다.</summary>
void loop()
{
    scanWifi();
    BLEScan *scanner = BLEDevice::getScan();
    BLEScanResults *results = scanner->start(5, false);
    Serial.printf("BLE devices: %d\n", results->getCount());
    for (int i = 0; i < results->getCount(); i++)
    {
        BLEAdvertisedDevice device = results->getDevice(i);
        Serial.printf("%s / %d dBm / %s\n", device.getAddress().toString().c_str(), device.getRSSI(), device.getName().c_str());
    }
    scanner->clearResults();
    WiFi.scanDelete();
    Serial.println("Next scan in 10 seconds. Results remain on this serial console only.");
    delay(10000);
}
