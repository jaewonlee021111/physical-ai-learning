"""MCP 2025-11-25 stdio: JSON-RPC 한 줄당 메시지 한 개. stdout에는 프로토콜만 쓴다."""
import json
import os
from pathlib import Path
import sys
import urllib.error
import urllib.request

BASE = Path(__file__).resolve().parents[1]
DOCUMENTS = {
    "requirements": BASE / "projects/equipment-loan/docs/requirements.md",
    "design": BASE / "projects/equipment-loan/docs/design.md",
    "handoff": BASE / "projects/equipment-loan/docs/handoff.md",
}


def text_result(text, error=False):
    return {"content": [{"type": "text", "text": text}], "isError": error}


def notion_read(page_id):
    # 토큰은 환경에서만 읽고 결과나 로그에 기록하지 않는다.
    token = os.environ.get("NOTION_TOKEN")
    if not token:
        raise ValueError("NOTION_TOKEN이 설정되지 않았습니다. 외부 호출은 수행하지 않았습니다.")
    compact = page_id.replace("-", "")
    if len(compact) != 32 or any(ch not in "0123456789abcdefABCDEF" for ch in compact):
        raise ValueError("Notion page_id 형식을 확인하세요.")
    request = urllib.request.Request(
        f"https://api.notion.com/v1/pages/{page_id}",
        headers={"Authorization": "Bearer " + token, "Notion-Version": "2025-09-03"},
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        page = json.load(response)
    title = []
    for prop in page.get("properties", {}).values():
        if prop.get("type") == "title":
            title.extend(piece.get("plain_text", "") for piece in prop.get("title", []))
    return {"id": page.get("id"), "url": page.get("url"), "title": "".join(title),
            "last_edited_time": page.get("last_edited_time")}


def dispatch(message):
    identifier = message.get("id")
    method = message.get("method")
    params = message.get("params", {})
    if identifier is None:
        return None  # initialized 등 알림에는 응답하지 않는다.
    result = None
    if method == "initialize":
        result = {"protocolVersion": "2025-11-25", "capabilities": {"tools": {}},
                  "serverInfo": {"name": "physical-ai-document-lab", "version": "1.0.0"}}
    elif method == "ping":
        result = {}
    elif method == "tools/list":
        result = {"tools": [
            {"name": "list_project_documents", "description": "실습 프로젝트의 읽기 가능한 문서 이름 목록", "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False}},
            {"name": "read_project_document", "description": "허용된 프로젝트 문서를 실제 파일에서 읽는다.", "inputSchema": {"type": "object", "properties": {"name": {"type": "string", "enum": list(DOCUMENTS)}}, "required": ["name"], "additionalProperties": False}},
            {"name": "read_notion_page", "description": "NOTION_TOKEN 환경이 있는 경우 접근 권한을 가진 Notion 페이지 메타데이터를 읽는다.", "inputSchema": {"type": "object", "properties": {"page_id": {"type": "string"}}, "required": ["page_id"], "additionalProperties": False}}
        ]}
    elif method == "tools/call":
        name = params.get("name")
        args = params.get("arguments", {})
        try:
            if name == "list_project_documents":
                result = text_result(json.dumps(list(DOCUMENTS), ensure_ascii=False))
            elif name == "read_project_document":
                if args.get("name") not in DOCUMENTS:
                    raise ValueError("허용된 문서 이름을 선택하세요.")
                result = text_result(DOCUMENTS[args["name"]].read_text(encoding="utf-8"))
            elif name == "read_notion_page":
                result = text_result(json.dumps(notion_read(args.get("page_id", "")), ensure_ascii=False))
            else:
                return {"jsonrpc": "2.0", "id": identifier, "error": {"code": -32602, "message": "알 수 없는 도구"}}
        except (ValueError, OSError, urllib.error.URLError) as error:
            result = text_result(str(error), error=True)
    else:
        return {"jsonrpc": "2.0", "id": identifier, "error": {"code": -32601, "message": "지원하지 않는 메서드"}}
    return {"jsonrpc": "2.0", "id": identifier, "result": result}


def main():
    for line in sys.stdin:
        try:
            message = json.loads(line)
            if not isinstance(message, dict) or message.get("jsonrpc") != "2.0" or not isinstance(message.get("method"), str):
                reply = {"jsonrpc": "2.0", "id": None, "error": {"code": -32600, "message": "잘못된 요청"}}
            else:
                reply = dispatch(message)
        except (json.JSONDecodeError, TypeError):
            reply = {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "JSON 파싱 오류"}}
        if reply is not None:
            print(json.dumps(reply, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
