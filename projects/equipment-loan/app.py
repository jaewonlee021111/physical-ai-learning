"""python app.py list | borrow CAM01 | return CAM01 [--data FILE]"""
import argparse
from pathlib import Path
from inventory import load, transact


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["list", "borrow", "return"])
    parser.add_argument("identifier", nargs="?")
    parser.add_argument("--data", type=Path, default=Path(__file__).resolve().parent / "data/equipment.json")
    args = parser.parse_args()
    try:
        if args.action == "list":
            items = load(args.data)
        else:
            items = transact(args.data, args.identifier, args.action)
            print("대여 완료" if args.action == "borrow" else "반납 완료")
        print("장비 ID | 이름 | 전체 | 남은 수량")
        for item in items:
            print(f"{item['id']} | {item['name']} | {item['total']} | {item['available']}")
    except (OSError, ValueError, UnicodeError) as error:
        print(f"처리 실패: {error}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
