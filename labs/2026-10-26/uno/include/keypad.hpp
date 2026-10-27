#pragma once
// 행 R1~R4=D2~D5, 열 C1~C4=D6~D9. 미선택 행은 고임피던스다.
const uint8_t rows[4] = {2,3,4,5};
const uint8_t cols[4] = {6,7,8,9};
/// <summary>한 행씩 LOW로 만들어 눌린 키를 찾는다. 다중 키는 거부한다.</summary>
int scanKey()
{
    int found = -1;
    for (uint8_t r = 0; r < 4; r++)
    {
        pinMode(rows[r], OUTPUT);
        digitalWrite(rows[r], LOW);
        delayMicroseconds(5);
        for (uint8_t c = 0; c < 4; c++)
        {
            if (digitalRead(cols[c]) == LOW)
            {
                if (found != -1)
                {
                    pinMode(rows[r], INPUT);
                    return -1;
                }
                found = r * 4 + c;
            }
        }
        pinMode(rows[r], INPUT);
    }
    return found;
}
/// <summary>행·열과 내부 풀업을 준비한다.</summary>
void setupKeys()
{
    for (uint8_t i = 0; i < 4; i++)
    {
        pinMode(rows[i], INPUT);
        pinMode(cols[i], INPUT_PULLUP);
    }
}
/// <summary>25ms 동안 안정된 단일 키를 반환한다. 미접촉은 -1이다.</summary>
int stableKey()
{
    static int candidate = -1;
    static int stable = -1;
    static uint32_t changed = 0;
    int key = scanKey();
    if (key != candidate)
    {
        candidate = key;
        changed = millis();
    }
    if (millis() - changed >= 25)
    {
        stable = candidate;
    }
    return stable;
}
