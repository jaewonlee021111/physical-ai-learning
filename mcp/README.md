# 실제 MCP stdio 실습

Python 표준 라이브러리만으로 JSON-RPC를 주고받는 서버·클라이언트다. 지원 규격은 MCP 2025-11-25 stdio로 명시하며, 모든 최신 규격 기능을 제공하는 SDK라는 뜻은 아니다.

```sh
python mcp/client_demo.py
```

별도 서버 프로세스를 시작하고 initialize → initialized 알림 → tools/list → tools/call을 수행한다. `requirements` 문서를 디스크에서 실제로 읽고, 허용 목록 밖 경로를 거절하는지 확인한다. 실제 요청·응답은 [evidence/mcp-transcript.json](../evidence/mcp-transcript.json)에 저장된다.

서버를 지원 클라이언트에 추가할 때 실행 파일은 `python`, 인자는 이 저장소의 절대 경로에 있는 `physical-ai/mcp/server.py`다. 로그인 토큰은 코드·JSON 설정 파일에 적지 말고 클라이언트의 비밀 환경변수 기능으로 전달한다.

## Notion 원격 읽기

`read_notion_page` 도구도 구현되어 있다. 본인 Notion integration에 공유한 페이지와 `NOTION_TOKEN` 환경변수가 있어야 실제 호출된다. 페이지 메타데이터·제목을 읽는 기능이며 본문 전체 조회·쓰기 기능은 제공하지 않는다. 직접 구현한 서버의 NOTION_TOKEN 어댑터는 별도 사용자 토큰을 받지 않아 실행하지 않았다. 연결된 Notion MCP로는 개인 비공개 실습 문서를 생성하고 실제로 다시 읽어 확인했다. 로컬 문서 호출 성공을 Notion 호출 성공으로 표시하지 않는다.

참고: [MCP stdio 규격](https://modelcontextprotocol.io/specification/2025-11-25/basic/transports), [Notion 페이지 조회](https://developers.notion.com/reference/retrieve-a-page).

## 실제 Notion 연결 확인
Notion MCP 검색·개인 비공개 문서 생성·본문 읽기에 성공했다. 문서의 학습 저장소·구현 목록·검증 결과·수정 내역을 다시 읽어 확인했다. 개인 페이지의 ID와 본문 전체는 공개 저장소에 복사하지 않는다. [호출 확인 기록](../evidence/notion-connection.json)
