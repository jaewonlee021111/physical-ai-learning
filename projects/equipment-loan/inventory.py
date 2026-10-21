"""장비 이름·전체·남은 수량, 대여·반납, JSON 복원."""
from copy import deepcopy
import json
import os
from pathlib import Path
import tempfile


def validate(items):
    if type(items) is not list:
        raise ValueError("장비 목록은 배열이어야 합니다.")
    seen = set()
    for item in items:
        if type(item) is not dict:
            raise ValueError("장비 항목은 객체여야 합니다.")
        if type(item.get("id")) is not str or not item["id"].strip() or item["id"] in seen:
            raise ValueError("장비 ID 누락 또는 중복")
        if type(item.get("name")) is not str or not item["name"].strip():
            raise ValueError("장비 이름 누락")
        if type(item.get("total")) is not int or type(item.get("available")) is not int:
            raise ValueError("수량은 정수여야 합니다.")
        if not 0 <= item["available"] <= item["total"]:
            raise ValueError("수량 범위 오류")
        seen.add(item["id"])
    return items


def load(path):
    return validate(json.loads(Path(path).read_text(encoding="utf-8")))


def change(items, identifier, action):
    validate(items)
    if action not in {"borrow", "return"}:
        raise ValueError("알 수 없는 동작")
    if not identifier or not identifier.strip():
        raise ValueError("장비를 선택하세요.")
    result = deepcopy(items)
    item = next((item for item in result if item["id"] == identifier), None)
    if item is None:
        raise ValueError("없는 장비 번호")
    if action == "borrow":
        if item["available"] == 0:
            raise ValueError("대여 가능한 재고 없음")
        item["available"] -= 1
    else:
        if item["available"] == item["total"]:
            raise ValueError("전체 수량 초과 반납 불가")
        item["available"] += 1
    return result


def save(path, items):
    validate(items)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, delete=False) as handle:
            temp = Path(handle.name)
            json.dump(items, handle, ensure_ascii=False, indent=2, allow_nan=False)
            handle.write("\n")
        os.replace(temp, path)
    finally:
        if temp is not None:
            temp.unlink(missing_ok=True)


def transact(path, identifier, action):
    items = load(path)
    updated = change(items, identifier, action)
    save(path, updated)
    return updated
