"""실제 별도 MCP 프로세스에 초기화·도구 목록·문서 읽기를 요청하고 응답을 검증."""
import json
from pathlib import Path
import subprocess
import sys

BASE = Path(__file__).resolve().parent


def demonstrate():
    requests = [
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-11-25", "capabilities": {}, "clientInfo": {"name": "lab-client", "version": "1.0"}}},
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
        {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "read_project_document", "arguments": {"name": "requirements"}}},
        {"jsonrpc": "2.0", "id": 4, "method": "tools/call", "params": {"name": "read_project_document", "arguments": {"name": "../../secret"}}},
    ]
    payload = "\n".join(json.dumps(row) for row in requests) + "\n"
    result = subprocess.run([sys.executable, str(BASE / "server.py")], input=payload, capture_output=True, text=True, timeout=10, check=True)
    replies = [json.loads(line) for line in result.stdout.splitlines()]
    assert [row["id"] for row in replies] == [1, 2, 3, 4]
    assert "R01" in replies[2]["result"]["content"][0]["text"]
    assert not replies[2]["result"]["isError"]
    assert replies[3]["result"]["isError"]
    return {"transport": "stdio", "protocol": "2025-11-25", "requests": requests, "responses": replies,
            "notion_remote_read": "not_run: no authorized page/token provided"}


if __name__ == "__main__":
    report = demonstrate()
    output = BASE.parent / "evidence/mcp-transcript.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("MCP 초기화·도구 목록·실제 파일 읽기·허용 목록 검증 성공")
