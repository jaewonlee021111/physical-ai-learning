# 2026-10-28 · Edge AI 이미지 분류와 팀 프로젝트 협업

사용자가 제공한 10월 28일 Zoom 녹화의 자동 자막 829개 항목과 강사 채팅을 확인하고, 핵심 공유 화면을 대조했다. 아래는 시간대별 나열 없이 주제별로 정리한 내용이다. 전체 영상을 매 순간 시청한 기록은 아니며 자막의 누락·오인식과 실물 확인 범위는 [SOURCES](SOURCES.md)에 구분했다.

## 이번 수업에서 한 것

| 주제 | 수업 내용 | 이 폴더의 산출물 |
| --- | --- | --- |
| 데이터 수집 | 전날 시작한 사진 데이터셋 수집 마무리 | JPEG 수집·세션별 폴더·입력 검사 도구 |
| Edge Impulse 학습 | 이미지 처리·전이학습·모델 크기·혼동행렬 | 재현 절차·설정 기록 양식·평가 코드 |
| ESP32 추론 | 학습 모델을 Arduino 라이브러리로 내보내 보드에서 실행·로컬 웹으로 관측 | XIAO ESP32S3 Sense 카메라 추론·웹 관측 펌웨어 소스 |
| 오분류 개선 | 배경·조명·각도에 따른 실패를 보고 추가 수집·재학습 | 데이터 점검·별도 촬영 세션 시험·재학습 확인표 |
| 팀 프로젝트 기획 | 역할·모임·주제 선정·하드웨어 범위·발표 | 아이디어 그룹화·백로그·발표·일정 정리 |
| GitHub 협업 | 팀 저장소·협업자·clone/pull·브랜치·PR·merge | 실제 취미 PR 연결·로컬 재현 스크립트 |
| 원격 협업 | 스프린트 계획·매일 공유·리뷰·비동기 영상 | 팀 작업·공유 양식 |
| 라즈베리파이 | OS 이미지 기록·SSH·Connect·전원·초기 접속 | 초기 설정·실패 원인 분리 가이드 |

## 직접 실행

Python 3.10 이상, 아래 명령은 저장소 루트에서 실행한다.

```sh
python -m pip install -r labs/2026-10-28/requirements.txt
python -m unittest discover -s labs/2026-10-28/tests -v
python labs/2026-10-28/tools/git_practice.py
```

실제 카메라 JPEG 주소를 알고 있으면 사진을 모을 수 있다. 아래 IP는 본인 보드의 주소로 바꾼다. 기존 10/23 카메라는 포트 81의 `/capture`를 사용할 수 있다.

```sh
python labs/2026-10-28/tools/dataset.py capture --url http://BOARD_IP:81/capture --label cola --session day1 --count 30
python labs/2026-10-28/tools/dataset.py capture --url http://BOARD_IP:81/capture --label cookie --session day1 --count 50
python labs/2026-10-28/tools/dataset.py capture --url http://BOARD_IP:81/capture --label background --session day1 --count 80
```

위 장수는 수업의 추가 수집 사례를 따라 쓴 실행 예다. 합격에 필요한 고정 장수가 아니다. 다른 조명·배경·각도로 `day2` 등을 따로 찍고 모든 클래스에 학습·시험 세션이 있도록 한다. 연속 프레임을 무작위로 나눠 유사 사진이 양쪽에 들어가는 일을 피한다.

```sh
python labs/2026-10-28/tools/dataset.py audit runtime/images --test-session day2 --out runtime/manifest.json
python labs/2026-10-28/tools/evaluate.py runtime/predictions.jsonl --labels background cola cookie
```

`runtime/images`는 실행 디렉터리 기준이다. 개인정보·실제 촬영 사진·API 키·학습 모델은 공개 커밋하지 않는다. 데이터 점검 결과 `valid`는 구조·중복 검사 결과이며 모델 품질 합격 판정이 아니다.

## 실행·검증 상태

- 데이터 수집/점검·평가: **11개 검사 통과**, 로컬 HTTP 서버에서 실제 JPEG 요청·저장 포함. 입력 사진은 검사에서 생성한 이미지이며 강의 물체 사진이 아니다.
- Git: 임시 로컬 저장소에서 브랜치·커밋·diff·병합을 실제 실행했다. 이 스크립트는 외부 GitHub에 push하지 않는다.
- 기존 팀 취미 작업: [팀원2 축구 시청 PR #2](https://github.com/rlacksals0618-collab/TEAMPRACTICE/pull/2)는 10월 28일 병합 완료로 10월 30일 API에서 확인했다. 이번 작업에서 새로 병합한 것은 아니다.
- 펌웨어: **소스 작성, 컴파일·업로드 미수행**. 사용자의 Edge Impulse 내보내기 라이브러리와 실물 보드가 필요하다. 가짜 모델로 빌드 성공을 만들지 않았다.
- Edge Impulse 실제 계정 학습·모델 내보내기, 실제 물체 추론·라즈베리파이 설정: **NOT_RUN**. 원본 사진·모델·프로젝트 인증 정보와 장비가 제공되지 않았다.

[검증 JSON](evidence/validation.json) · [실제 Git 실행 로그](evidence/git-practice.json)

## 자세히 보기

[이미지 학습·재학습](EDGE-AI.md) · [펌웨어 실행](firmware/README.md) · [팀 협업·발표](TEAMWORK.md) · [라즈베리파이](RASPBERRY-PI.md) · [출처·정정](SOURCES.md)
