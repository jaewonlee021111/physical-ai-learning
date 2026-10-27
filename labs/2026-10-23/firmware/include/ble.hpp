#pragma once
#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLE2902.h>
// 이 실습용 사용자 정의 UUID이며 Bluetooth SIG의 표준 프로파일이라고 주장하지 않는다.
#define LAB_SERVICE "34cf0001-5a3b-4ab9-9469-e152c1b37c01"
#define LAB_TOUCH "34cf0002-5a3b-4ab9-9469-e152c1b37c01"
#define LAB_LED "34cf0003-5a3b-4ab9-9469-e152c1b37c01"
static BLECharacteristic *touchCharacteristic;
static BLECharacteristic *ledCharacteristic;
static volatile bool bleConnected = false;
static volatile int pendingLed = -1;

/// <summary>연결 상태를 추적하고 연결이 끊기면 다시 광고한다.</summary>
class ConnectionCallbacks : public BLEServerCallbacks
{
    void onConnect(BLEServer *server) override
    {
        bleConnected = true;
    }
    void onDisconnect(BLEServer *server) override
    {
        bleConnected = false;
        server->startAdvertising();
    }
};

/// <summary>LED 특성의 0 또는 1 쓰기만 허용한다.</summary>
class LedCallbacks : public BLECharacteristicCallbacks
{
    void onWrite(BLECharacteristic *characteristic) override
    {
        String value = characteristic->getValue();
        if (value == "0" || value == "1")
        {
            pendingLed = value == "1" ? 1 : 0;
        }
    }
};

/// <summary>스마트폰에서 읽기·쓰기·구독할 BLE GATT 서비스를 준비한다.</summary>
void setup()
{
    Serial.begin(115200);
    setupTouch();
    BLEDevice::init("PhysicalAI-Touch");
    BLEServer *server = BLEDevice::createServer();
    server->setCallbacks(new ConnectionCallbacks());
    BLEService *service = server->createService(LAB_SERVICE);
    touchCharacteristic = service->createCharacteristic(LAB_TOUCH, BLECharacteristic::PROPERTY_READ | BLECharacteristic::PROPERTY_NOTIFY);
    touchCharacteristic->addDescriptor(new BLE2902());
    touchCharacteristic->setValue("0");
    ledCharacteristic = service->createCharacteristic(LAB_LED, BLECharacteristic::PROPERTY_READ | BLECharacteristic::PROPERTY_WRITE | BLECharacteristic::PROPERTY_NOTIFY);
    ledCharacteristic->addDescriptor(new BLE2902());
    ledCharacteristic->setCallbacks(new LedCallbacks());
    ledCharacteristic->setValue("0");
    service->start();
    BLEAdvertising *advertising = BLEDevice::getAdvertising();
    advertising->addServiceUUID(LAB_SERVICE);
    advertising->setScanResponse(true);
    advertising->start();
    Serial.println("BLE advertising PhysicalAI-Touch. Values are ASCII 0/1. Use nRF Connect or web/ble.html.");
}
/// <summary>터치 알림과 LED 쓰기를 반영한다. 알림은 변경될 때만 보낸다.</summary>
void loop()
{
    bool changed = pollTouch();
    if (changed)
    {
        setLed(touched);
        touchCharacteristic->setValue(touched ? "1" : "0");
        if (bleConnected)
        {
            touchCharacteristic->notify();
        }
    }
    if (pendingLed >= 0)
    {
        int value = pendingLed;
        pendingLed = -1;
        setLed(value == 1);
        changed = true;
    }
    if (changed)
    {
        ledCharacteristic->setValue(ledOn ? "1" : "0");
        if (bleConnected)
        {
            ledCharacteristic->notify();
        }
    }
    delay(10);
}
