# 검증 기록 · 2026-10-27

대상 코드 커밋: `e511bbfa4760e0d5636bba8ee6a2a3a4c96660ee`.

| 검사 | 결과·증거 |
|---|---|
| PlatformIO 펌웨어 8종 | scanner / blink / touch / sta / ap / ble / camera / cloud 모두 컴파일 성공 |
| 원격 영상 입력 | Python 5개 테스트 성공: 분할 JPEG·버퍼 제한·URL 검증·실제 HTTP JPEG 수신에서 Flask 캡처까지·연결 실패 |
| 기존 비전 회귀 검사 | 15개 테스트 성공 |
| 기존 10/22 전체 CI | 성공: 기존 보드 빌드와 브라우저 검사 포함 |

- [10/23 컴파일·게이트웨이 CI](https://github.com/jaewonlee021111/physical-ai-learning/actions/runs/40487167086)
- [10/22 회귀 CI](https://github.com/jaewonlee021111/physical-ai-learning/actions/runs/40487180116)

HTTP 통합 테스트는 테스트 서버가 제공하는 JPEG를 실제 요청·디코딩한 것이다. ESP32 카메라 영상이나 무선 링크를 시험한 것으로 해석하지 않는다. 테스트에서 실제 YOLO 모델 추론을 새로 실행한 것은 아니며 이전 날짜의 검출기 구현을 재사용한다.

이 환경에는 사용자 ESP32·터치 도선·카메라·휴대폰이 연결되어 있지 않다. 따라서 실제 업로드·센서 값·카메라 FPS·BLE 연결과 본인 Supabase/Tailscale 계정 연결은 미검증이다. 각 실습 README 순서로 사용자 장비에서 확인한다. 성공 로그·사진을 임의로 만들지 않았다.
