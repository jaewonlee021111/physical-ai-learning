#include <Arduino.h>
// 모드는 각각 독립 회로다. 한꺼번에 모든 부품을 연결하지 않는다.
#if LAB_MODE == 0
/// <summary>UNO USB 연결·업로드·시리얼을 확인한다.</summary>
void setup()
{
    Serial.begin(115200);
    pinMode(LED_BUILTIN, OUTPUT);
    Serial.println(F("UNO_READY 115200"));
}
/// <summary>하트비트를 보내 실제 실행 여부를 확인한다.</summary>
void loop()
{
    digitalWrite(LED_BUILTIN, !digitalRead(LED_BUILTIN));
    Serial.print(F("UPTIME_MS ")); Serial.println(millis());
    delay(1000);
}
#elif LAB_MODE == 1
const uint8_t rgbPins[3] = {9,10,11};
int channels[3] = {255,80,0};
char line[48]; uint8_t used = 0;
/// <summary>공통 음극 RGB의 3채널 PWM을 준비한다.</summary>
void setup()
{
    Serial.begin(115200);
    for (uint8_t p : rgbPins)
    {
        pinMode(p, OUTPUT);
    }
    Serial.println(F("RGB_READY send: RGB 255 80 0"));
}
/// <summary>0~255 입력을 검증하고 1초 켜짐·1초 꺼짐을 반복한다.</summary>
void loop()
{
    while (Serial.available())
    {
        char c = Serial.read();
        if (c == '\n')
        {
            line[used] = 0;
            int r,g,b; char extra;
            if (sscanf(line,"RGB %d %d %d %c", &r,&g,&b,&extra) == 3 && r>=0 && r<=255 && g>=0 && g<=255 && b>=0 && b<=255)
            {
                channels[0]=r; channels[1]=g; channels[2]=b;
                Serial.println(F("RGB_OK"));
            }
            else
            {
                Serial.println(F("ERR RGB requires three integers 0..255"));
            }
            used = 0;
        }
        else if (c != '\r' && used < sizeof(line)-1)
        {
            line[used++] = c;
        }
    }
    bool on = (millis()/1000)%2 == 0;
    for (uint8_t i=0;i<3;i++)
    {
        analogWrite(rgbPins[i],on ? channels[i] : 0);
    }
}
#elif LAB_MODE == 2 || LAB_MODE == 3
#include <Wire.h>
#include <LiquidCrystal_I2C.h>
#if LAB_MODE == 3
#include <DHT.h>
#include <TimeLib.h>
DHT dht(2,DHT11);
float temperature = NAN, humidity = NAN;
char timeLine[32]; uint8_t timeUsed = 0;
#endif
LiquidCrystal_I2C *lcd = nullptr;
/// <summary>PCF8574의 일반 주소를 탐색해 LCD를 준비한다.</summary>
void setup()
{
    Serial.begin(115200); Wire.begin();
    uint8_t address = 0;
    for (uint8_t a=0x20;a<=0x3f;a++)
    {
        Wire.beginTransmission(a);
        if (Wire.endTransmission()==0)
        {
            Serial.print(F("I2C 0x")); Serial.println(a,HEX);
            if (a==0x27 || a==0x3f)
            {
                address=a;
            }
        }
    }
    if (!address)
    {
        Serial.println(F("LCD_NOT_FOUND: check wiring/address/contrast")); return;
    }
    lcd = new LiquidCrystal_I2C(address,16,2);
    lcd->init(); lcd->backlight(); lcd->print(F("hello, world"));
#if LAB_MODE == 3
    dht.begin();
    Serial.println(F("TIME_REQUIRED send: TIME <UTC Unix seconds>; LCD shows KST"));
#endif
}
/// <summary>센서는 2초, LCD 시계는 매초 갱신한다. UNO에 실제 시계가 있다고 가정하지 않는다.</summary>
void loop()
{
#if LAB_MODE == 3
    while (Serial.available())
    {
        char c=Serial.read();
        if (c=='\n')
        {
            timeLine[timeUsed]=0;
            char *end=nullptr;
            unsigned long stamp = timeUsed >= 6 ? strtoul(timeLine+5,&end,10) : 0;
            if (timeUsed >= 6 && strncmp(timeLine,"TIME ",5)==0 && end!=timeLine+5 && *end==0 && stamp>=1704067200UL && stamp<=4102444800UL)
            {
                setTime(stamp); Serial.println(F("TIME_OK"));
            }
            else
            {
                Serial.println(F("ERR TIME"));
            }
            timeUsed=0;
        }
        else if (c!='\r' && timeUsed<sizeof(timeLine)-1)
        {
            timeLine[timeUsed++]=c;
        }
    }
    static uint32_t sensorAt=0, screenAt=0;
    if (millis()-sensorAt>=2000)
    {
        sensorAt=millis(); temperature=dht.readTemperature(); humidity=dht.readHumidity();
        if (isnan(temperature) || isnan(humidity))
        {
            Serial.println(F("DHT_ERROR"));
        }
    }
    if (millis()-screenAt>=1000)
    {
        screenAt=millis();
        char row[17];
        if (timeStatus()==timeNotSet)
        {
            strcpy(row,"Sync PC time    ");
        }
        else
        {
            time_t kst=now()+9UL*3600UL;
            snprintf(row,sizeof(row),"%02d/%02d %02d:%02d:%02d",month(kst),day(kst),hour(kst),minute(kst),second(kst));
            Serial.print(year(kst)); Serial.print('-'); Serial.print(row); Serial.println(F(" KST"));
        }
        if (lcd)
        {
            lcd->setCursor(0,0); lcd->print(F("                ")); lcd->setCursor(0,0); lcd->print(row);
            lcd->setCursor(0,1); lcd->print(F("                ")); lcd->setCursor(0,1);
            if (isnan(temperature) || isnan(humidity))
            {
                lcd->print(F("DHT read error"));
            }
            else
            {
                lcd->print(F("T:"));lcd->print(temperature,1);lcd->print(F("C H:"));lcd->print(humidity,0);lcd->print('%');
            }
        }
    }
#endif
}
#elif LAB_MODE == 4
uint32_t seq=0;
const uint8_t buttonPins[3]={3,6,2};
bool buttons[3]={false,false,false}, candidates[3]={false,false,false};
uint32_t changed[3]={0,0,0};
/// <summary>조이스틱과 두 버튼의 풀업 입력을 준비한다.</summary>
void setup()
{
    Serial.begin(115200);
    for (uint8_t pin:buttonPins)
    {
        pinMode(pin,INPUT_PULLUP);
    }
}
/// <summary>50Hz JSON Lines를 보낸다. ADC 원본과 눌림 상태를 보존한다.</summary>
void loop()
{
    for (uint8_t i=0;i<3;i++)
    {
        bool next=digitalRead(buttonPins[i])==LOW;
        if (next!=candidates[i])
        {
            candidates[i]=next;changed[i]=millis();
        }
        if (millis()-changed[i]>=20)
        {
            buttons[i]=next;
        }
    }
    static uint32_t sent=0;
    if (millis()-sent>=20)
    {
        sent=millis();
        Serial.print(F("{\"type\":\"input\",\"seq\":"));Serial.print(seq++);
        Serial.print(F(",\"x\":"));Serial.print(analogRead(A0));
        Serial.print(F(",\"y\":"));Serial.print(analogRead(A1));
        Serial.print(F(",\"jump\":"));Serial.print(buttons[0]);
        Serial.print(F(",\"attack\":"));Serial.print(buttons[1]);
        Serial.print(F(",\"bomb\":"));Serial.print(buttons[2]);Serial.println('}');
    }
}
#elif LAB_MODE == 5 || LAB_MODE == 6
#include "keypad.hpp"
const uint16_t notes[16]={262,294,330,349,392,440,494,523,587,659,698,784,880,988,1047,1175};
/// <summary>16키 단음 입력을 준비한다. 부저는 충돌 없는 D10이다.</summary>
void setup()
{
    Serial.begin(115200);setupKeys();pinMode(10,OUTPUT);
}
/// <summary>키 변화만 출력하고 누르는 동안 해당 주파수의 음을 유지한다.</summary>
void loop()
{
    static int previous=-1;
    int key=stableKey();
    if (key!=previous)
    {
        Serial.print(F("KEY "));Serial.println(key+1);
#if LAB_MODE == 6
        if (key>=0)
        {
            tone(10,notes[key]);
        }
        else
        {
            noTone(10);
        }
#endif
        previous=key;
    }
}
#elif LAB_MODE == 7
#include <IRremote.hpp>
/// <summary>실물 핀표를 대조한 IR 수신기의 OUT을 D2로 받는다.</summary>
void setup()
{
    Serial.begin(115200);IrReceiver.begin(2,DISABLE_LED_FEEDBACK);
}
/// <summary>프로토콜·주소·명령·반복 여부를 출력하고 수신을 재개한다.</summary>
void loop()
{
    if (IrReceiver.decode())
    {
        IrReceiver.printIRResultShort(&Serial);
        Serial.print(F(" repeat="));Serial.println((IrReceiver.decodedIRData.flags & IRDATA_FLAGS_IS_REPEAT)!=0);
        IrReceiver.resume();
    }
}
#elif LAB_MODE == 8
#include <math.h>
float threshold=40.0f;
char soundLine[32]; uint8_t soundUsed=0;
/// <summary>AO 신호를 읽는다. 보정되지 않은 모듈로 dB SPL을 주장하지 않는다.</summary>
void setup()
{
    Serial.begin(115200);Serial.println(F("SOUND_READY: RMS ADC / relative dBFS; THRESH 40"));
}
/// <summary>50ms 표본에서 DC를 제거한 RMS와 ADC 기준 dBFS를 계산한다.</summary>
void loop()
{
    while (Serial.available())
    {
        char c=Serial.read();
        if (c=='\n')
        {
            soundLine[soundUsed]=0;char *end=nullptr;
            float value=soundUsed>=8 ? strtod(soundLine+7,&end) : -1;
            if (soundUsed>=8 && strncmp(soundLine,"THRESH ",7)==0 && end!=soundLine+7 && *end==0 && isfinite(value) && value>=0 && value<=512)
            {
                threshold=value;
            }
            soundUsed=0;
        }
        else if (c!='\r' && soundUsed<sizeof(soundLine)-1)
        {
            soundLine[soundUsed++]=c;
        }
    }
    uint32_t start=millis(), count=0; double sum=0,squares=0;
    while (millis()-start<50)
    {
        int value=analogRead(A0);sum+=value;squares+=(double)value*value;count++;
    }
    double mean=sum/count;
    float rms=sqrt(max(0.0,squares/count-mean*mean));
    float dbfs=rms>0 ? 20.0f*log10(rms/511.5f) : -120.0f;
    bool alarm=rms>threshold;
    Serial.print(alarm ? F("\033[31mALARM ") : F("\033[0mSOUND "));
    Serial.print(F("RMS_ADC="));Serial.print(rms,1);Serial.print(F(" dBFS="));Serial.print(dbfs,1);
    Serial.print(F(" THRESH="));Serial.print(threshold,1);Serial.println(F("\033[0m"));
    delay(100);
}
#endif
