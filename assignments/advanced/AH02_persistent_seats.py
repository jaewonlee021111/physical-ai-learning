"""AH02: 손상된 상태 파일을 초기화하지 않고 예약 상태를 원자적으로 저장."""
import argparse
import json
import os
from pathlib import Path
import sys
import tempfile

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE.parent / "basic"))
from HW02_seats import run


def load_state(path):
    path = Path(path)
    if not path.exists():
        return [False] * 5
    state = json.loads(path.read_text(encoding="utf-8"))
    if type(state) is not list or len(state) != 5 or any(type(item) is not bool for item in state):
        raise ValueError("저장파일 오류")
    return state


def save_state(path, state):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, delete=False) as handle:
            temporary = Path(handle.name)
            json.dump(state, handle)
            handle.write("\n")
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state", type=Path, default=BASE / "work/seats.json")
    args = parser.parse_args()
    try:
        seats = load_state(args.state)
        run(seats, lambda values: save_state(args.state, values))
    except (OSError, UnicodeError, ValueError):
        print("저장파일 오류")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
