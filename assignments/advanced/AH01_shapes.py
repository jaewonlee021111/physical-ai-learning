"""AH01: JSON 설정 검사 → 도형 생성 → UTF-8 저장."""
import argparse
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent


def read_config(path):
    config = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(config, dict):
        raise ValueError("설정 오류")
    shape, height, char = config.get("shape"), config.get("height"), config.get("char")
    if type(shape) is not str or shape not in {"tree", "diamond"}:
        raise ValueError("설정 오류")
    if type(height) is not int or not 3 <= height <= 15:
        raise ValueError("설정 오류")
    if type(char) is not str or char not in {"*", "#", "@"}:
        raise ValueError("설정 오류")
    return config


def make_lines(config):
    shape, height, char = config["shape"], config["height"], config["char"]
    lines = [" " * (height - i) + char * (2 * i - 1) for i in range(1, height + 1)]
    if shape == "tree":
        lines.append(" " * (height - 1) + "|")
    else:
        for i in range(height - 1, 0, -1):
            lines.append(" " * (height - i) + char * (2 * i - 1))
    return lines


def save_lines(lines, destination):
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=BASE / "data/shape.json")
    parser.add_argument("--output", type=Path, default=BASE / "work/shape.txt")
    args = parser.parse_args()
    try:
        config = read_config(args.config)
        lines = make_lines(config)
        save_lines(lines, args.output)
    except (OSError, UnicodeError, ValueError, TypeError):
        print("설정 오류")
        return 1
    print("도형 저장 완료")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
