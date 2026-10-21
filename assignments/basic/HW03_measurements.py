"""HW03: 정수 측정값 수집·요약. 기준 초과는 > 비교다."""


def parse_integer(raw):
    value = int(raw.strip())
    if not -1000 <= value <= 1000:
        raise ValueError("범위 오류")
    return value


def read_threshold():
    while True:
        try:
            return parse_integer(input())
        except ValueError:
            print("기준 오류")


def collect():
    values = []
    while True:
        raw = input().strip()
        if raw.lower() == "done":
            return values
        try:
            values.append(parse_integer(raw))
        except ValueError:
            print("입력 오류")


def summarize(values, threshold):
    if not values:
        return "측정값 없음"
    total = 0
    exceeded = 0
    for value in values:
        total += value
        if value > threshold:
            exceeded += 1
    ordered = sorted(values)
    mid = len(values) // 2
    median = ordered[mid] if len(values) % 2 else (ordered[mid - 1] + ordered[mid]) / 2
    # 중앙값은 심화 함수 결과에 보관하지만 필수 화면 출력에는 추가하지 않는다.
    result = {"count": len(values), "total": total, "mean": total / len(values),
              "maximum": max(values), "minimum": min(values), "exceeded": exceeded,
              "median": median}
    return "\n".join([f"개수 {result['count']}", f"합계 {total}", f"평균 {result['mean']:.2f}",
                       f"최댓값 {result['maximum']}", f"최솟값 {result['minimum']}", f"기준 초과 {exceeded}"])


if __name__ == "__main__":
    try:
        threshold = read_threshold()
        print(summarize(collect(), threshold))
    except EOFError:
        pass
