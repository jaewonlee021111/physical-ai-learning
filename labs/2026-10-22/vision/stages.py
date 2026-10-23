"""함수의 XML 설명과 실제 계측 결과를 대시보드에서 공유한다."""
from collections import deque
from functools import wraps
import inspect
import threading
from time import perf_counter
import xml.etree.ElementTree as ET
from contextvars import ContextVar

REGISTRY = {}
EVENTS = deque(maxlen=500)
LOCK = threading.Lock()
ACTIVE = "idle"
FRAME = ContextVar("frame", default=0)


def describe(value):
    """<summary>배열과 결과의 크기를 간단히 요약한다.</summary>
    <param name="value">입출력 값</param><input>배열·목록·바이트</input>
    <output>shape·dtype 또는 길이</output><reason>영상 전체를 로그에 복사하지 않는다.</reason>"""
    if hasattr(value, "shape"):
        return {"shape": list(value.shape), "dtype": str(value.dtype)}
    if isinstance(value, (bytes, list, tuple)):
        return {"type": type(value).__name__, "length": len(value)}
    return {"type": type(value).__name__}


def stage(name):
    """<summary>함수를 등록하고 실행 시간을 기록한다.</summary>
    <param name="name">단계 식별자</param><input>함수</input>
    <output>계측된 함수</output><reason>설명과 계측의 이름을 일치시키기 위해서다.</reason>"""
    def decorate(function):
        """<summary>원본 설명을 유지한 계측 함수를 만든다.</summary>
        <param name="function">대상 함수</param><input>함수</input><output>래퍼</output>
        <reason>inspect.getdoc이 원본 XML을 읽을 수 있어야 한다.</reason>"""
        REGISTRY[name] = function

        @wraps(function)
        def wrapped(*args, **kwargs):
            """<summary>호출의 시작·종료 시각을 기록한다.</summary>
            <param name="args">위치 인수</param><param name="kwargs">키워드 인수</param>
            <input>호출 인수</input><output>원본 반환값</output><reason>코드 흐름을 바꾸지 않고 계측한다.</reason>"""
            global ACTIVE
            start = perf_counter()
            with LOCK:
                previous = ACTIVE
                ACTIVE = name
            result = None
            try:
                result = function(*args, **kwargs)
                return result
            finally:
                end = perf_counter()
                with LOCK:
                    EVENTS.append({"stage": name, "frame": FRAME.get(), "start": start, "end": end,
                                   "ms": (end-start)*1000, "input": [describe(a) for a in args],
                                   "output": describe(result)})
                    ACTIVE = previous
        return wrapped
    return decorate


def metadata():
    """<summary>등록된 XML 설명을 JSON용 데이터로 변환한다.</summary>
    <input>함수 레지스트리</input><output>단계 설명 목록</output>
    <reason>노드 설명과 코드 주석이 서로 달라지는 것을 막는다.</reason>"""
    rows = []
    for name, function in REGISTRY.items():
        row = {"id": name, "label": name}
        try:
            root = ET.fromstring("<doc>" + (inspect.getdoc(function) or "") + "</doc>")
            row.update({key: root.findtext(key, "") for key in ("summary", "input", "output", "reason")})
            row["params"] = {p.get("name"): p.text for p in root.findall("param")}
        except ET.ParseError:
            import logging
            logging.warning("XML 설명 파싱 실패: %s", name)
        rows.append(row)
    return rows
