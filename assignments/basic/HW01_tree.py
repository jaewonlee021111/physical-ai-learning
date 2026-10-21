"""HW01: 입력 오류를 다시 묻고 높이 3~15의 트리와 | 줄기를 출력한다."""


def read_height():
    while True:
        try:
            height = int(input().strip())
            if 3 <= height <= 15:
                return height
        except ValueError:
            pass
        print("높이 오류")


def tree_lines(height):
    if type(height) is not int or not 3 <= height <= 15:
        raise ValueError("높이 오류")
    lines = []
    for row in range(1, height + 1):
        # 최대 너비 2H-1에서 별 2i-1을 빼면 양쪽 공백은 각각 H-i다.
        lines.append(" " * (height - row) + "*" * (2 * row - 1))
    lines.append(" " * (height - 1) + "|")
    return lines


def print_tree(height):
    print("\n".join(tree_lines(height)))


if __name__ == "__main__":
    try:
        print_tree(read_height())
    except EOFError:
        pass
