"""높이를 받아 줄기 포함 트리를 출력하는 복습 예제."""
import argparse


def render_tree(height, count=1):
    if height < 1 or count < 1:
        raise ValueError("높이와 트리 개수는 1 이상이어야 합니다.")
    width = 2 * height - 1
    rows = [("*" * (2 * row - 1)).center(width) for row in range(1, height + 1)]
    rows.append("*".center(width))
    return "\n".join("   ".join([row] * count).rstrip() for row in rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("height", type=int, nargs="?", help="잎 높이")
    parser.add_argument("--count", type=int, default=1)
    args = parser.parse_args()
    try:
        height = args.height if args.height is not None else int(input("트리 높이: "))
        print(render_tree(height, args.count))
    except ValueError as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()

