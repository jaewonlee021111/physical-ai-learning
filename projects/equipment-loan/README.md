# 실습실 장비 대여 관리

2026-10-20 코드 에이전트 수업의 R01~R05를 구현한 Python CLI 프로젝트입니다. 표준 라이브러리만 사용합니다.

저장소 루트에서:

```sh
python projects/equipment-loan/app.py list
python projects/equipment-loan/app.py borrow CAM01
python projects/equipment-loan/app.py return CAM01
python -m unittest discover -s projects/equipment-loan -v
```

기본 명령은 이 프로젝트의 data/equipment.json을 실제로 수정합니다. 연습용 사본은 `--data 사본경로`로 지정합니다. 대여 가능 수량 0, 미선택·없는 번호, 초과 반납, 손상된 JSON은 거절하고 자료를 보존합니다. 다중 사용자·동시 프로세스용 DB와 잠금은 제공하지 않는 단일 사용자 실습입니다.

요구사항·설계·검토·인수인계는 [docs](docs/requirements.md), 프로젝트 규칙은 [AGENTS.md](AGENTS.md), 재사용 검토 절차는 [.agents/skills/review-inventory/SKILL.md](.agents/skills/review-inventory/SKILL.md)에 있습니다.

[실제 로컬 MCP 문서 읽기 실습](../../mcp/README.md)도 이 프로젝트 문서를 대상으로 합니다.
