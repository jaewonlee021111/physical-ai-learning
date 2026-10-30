"""Run a disposable local team-branch exercise; no external repo changes."""
import json
import subprocess
import tempfile
from pathlib import Path


def practice():
    log = []
    with tempfile.TemporaryDirectory(prefix="oct28-git-") as folder:
        root = Path(folder)
        def git(*args):
            result = subprocess.run(["git", "-C", str(root), *args], check=True,
                                    text=True, capture_output=True)
            log.append({"command": "git " + " ".join(args), "output": result.stdout.strip()})
            return result.stdout.strip()
        git("init", "-b", "main")
        git("config", "user.name", "Local Practice")
        git("config", "user.email", "practice@example.invalid")
        (root / "README.md").write_text("# Team hobbies\n", encoding="utf-8")
        git("add", "README.md")
        git("commit", "-m", "Create team layout")
        git("switch", "-c", "member2/football")
        p = root / "members/member2"
        p.mkdir(parents=True)
        (p / "index.html").write_text('<!doctype html><html lang="ko"><meta charset="utf-8"><title>축구 시청</title><h1>축구 시청</h1><p>해외축구 경기를 보며 선수들의 플레이와 경기 흐름을 즐깁니다.</p></html>\n', encoding="utf-8")
        git("add", "members/member2/index.html")
        git("commit", "-m", "Add member2 football hobby")
        git("diff", "main...HEAD", "--stat")
        git("switch", "main")
        git("merge", "--no-ff", "member2/football", "-m", "Review and merge local practice")
        git("log", "--oneline", "--all", "--graph")
        assert "해외축구" in (p / "index.html").read_text(encoding="utf-8")
        assert git("status", "--porcelain") == ""
    return {"scope": "disposable local repo; no GitHub PR created by this script", "passed": True, "commands": log}


if __name__ == "__main__":
    print(json.dumps(practice(), ensure_ascii=False, indent=2))
