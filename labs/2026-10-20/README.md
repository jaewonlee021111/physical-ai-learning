# AI 코드 에이전트 실습

[실제 장비 대여 프로그램](../../projects/equipment-loan/README.md)에서 R01~R05를 구현했다. 대여·반납·재고 경계·저장·복원·실패 시 원본 보존을 테스트한다.

| 교안 단원 | 실제 결과 |
| --- | --- |
| E01~E05 도구·준비·계획·수정·실행 | README와 실행된 코드·evidence/validation.json |
| E06 요구사항 | projects/equipment-loan/docs/requirements.md |
| E07 화면·데이터·함수 설계 | projects/equipment-loan/docs/design.md |
| E08 요청문 | projects/equipment-loan/docs/task.md |
| E09~E10 컨텍스트·기록 | docs/handoff.md와 실제 실행 로그 |
| E11 프로젝트 규칙 | AGENTS.md |
| E12 반복 검토 Skill | .agents/skills/review-inventory/SKILL.md |
| E13~E14 연결 방식·MCP | ../../mcp/server.py와 실제 stdio 요청·응답 |
| E15 diff·테스트·오류 재현 | 6개 재고 테스트, Git diff·충돌 기록 |
| E16 변경·인수인계 | 원본 변경 방지·원자적 저장 구현, docs/handoff.md |

로컬 MCP 문서는 실제 읽었다. Notion MCP로 개인 비공개 검수 문서를 생성하고 본문을 실제로 읽어 확인했다. 사람 팀 검수는 별도다.

## 실제 Notion 연결 확인
Notion MCP 검색·개인 비공개 문서 생성·본문 읽기에 성공했다. 문서의 학습 저장소·구현 목록·검증 결과·수정 내역을 다시 읽어 확인했다. 개인 페이지의 ID와 본문 전체는 공개 저장소에 복사하지 않는다. [호출 확인 기록](../../evidence/notion-connection.json)
