"""HW02: 5개 좌석 예약·취소. 저장 방식 확장은 AH02에 있다."""


def show(seats):
    return " ".join(f"{i}:{'X' if taken else 'O'}" for i, taken in enumerate(seats, 1))


def change(seats, number, reserve):
    if type(number) is not int or not 1 <= number <= len(seats):
        return "좌석 오류"
    # 사람의 1번 좌석은 리스트의 0번 위치다.
    index = number - 1
    if seats[index] == reserve:
        return "이미 예약" if reserve else "빈 좌석"
    seats[index] = reserve
    return "예약 완료" if reserve else "취소 완료"


def run(seats=None, save=None):
    seats = [False] * 5 if seats is None else seats
    while True:
        try:
            command = input().strip()
        except EOFError:
            return
        if command == "0":
            print("종료")
            return
        if command == "1":
            print(show(seats))
        elif command in {"2", "3"}:
            try:
                number = int(input().strip())
            except ValueError:
                print("좌석 오류")
                continue
            except EOFError:
                return
            candidate = seats.copy()
            result = change(candidate, number, command == "2")
            if result in {"예약 완료", "취소 완료"}:
                # 파일 저장이 실패하면 현재 메모리 상태도 바꾸지 않는다.
                if save is not None:
                    save(candidate)
                seats[:] = candidate
            print(result)
        else:
            print("메뉴 오류")


if __name__ == "__main__":
    run()
