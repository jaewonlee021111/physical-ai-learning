"""무거운 영상·모델 모듈 없이 계측과 XML 설명을 관리한다."""
from collections import deque
from functools import wraps
import inspect
import logging
import math
import threading
from time import perf_counter
import xml.etree.ElementTree as ET
import config

LABELS=dict(capture="입력·디코딩",preprocess="전처리",inference="추론",postprocess="후처리",visualize="시각화",output="출력")


def parse_xml_docstring(function):
    """<summary>XML 주석을 읽어 단계 설명으로 변환한다.</summary><param name="function">대상 함수</param><input>함수</input><output>설명 사전</output><reason>UI 설명과 실제 코드의 근거를 공유한다.</reason>"""
    root=ET.fromstring("<doc>"+(inspect.getdoc(function) or "")+"</doc>")
    result={key:" ".join(root.findtext(key,"").split()) for key in ("summary","input","output","reason")}
    result["params"]=[dict(name=p.get("name",""),text=" ".join("".join(p.itertext()).split())) for p in root.findall("param")]
    return result


def describe(value):
    """<summary>입출력의 크기와 형식을 요약한다.</summary><param name="value">관찰할 값</param><input>배열·목록 등</input><output>짧은 문자열</output><reason>영상 전체를 로그에 넣지 않는다.</reason>"""
    if hasattr(value,"shape"):
        return f"shape={value.shape} dtype={value.dtype}"
    if isinstance(value,(bytes,list,tuple,dict)):
        return f"{type(value).__name__} count={len(value)}"
    return type(value).__name__


class Pipeline:
    """<summary>프레임별 시간과 로그를 동기화한다.</summary><input>단계 실행 기록</input><output>스냅샷</output><reason>수신·처리·HTTP 스레드가 공유한다.</reason>"""
    def __init__(self,window=config.STAT_WINDOW,log_maxlen=config.LOG_MAXLEN,log_every=config.LOG_EVERY):
        """<summary>인스턴스 설정과 동기화 자원을 준비한다.</summary><param name="window">window 인수</param><param name="log_maxlen">log_maxlen 인수</param><param name="log_every">log_every 인수</param><input>호출 인수 또는 공유 상태</input><output>처리 결과 또는 상태 갱신</output><reason>수업의 처리 흐름을 코드와 함께 설명하기 위해서다.</reason>"""
        self.lock=threading.RLock()
        self.registry={}
        self.events=deque(maxlen=log_maxlen)
        self.history=deque(maxlen=window)
        self.log_every=max(1,log_every)
        self.frame=0
        self.seq=0
        self.active="idle"
        self.current={}
        self.skipped=False
        self.last_skipped=False
        self.status={}
        self.counters=dict(frames=0,aborted=0,dropped=0,reconnects=0)
        self.started=0

    def begin_frame(self):
        """<summary>새 프레임의 계측을 시작한다.</summary><input>호출 인수 또는 공유 상태</input><output>처리 결과 또는 상태 갱신</output><reason>수업의 처리 흐름을 코드와 함께 설명하기 위해서다.</reason>"""
        with self.lock:
            self.frame+=1
            self.current={}
            self.skipped=False
            self.started=perf_counter()

    def end_frame(self):
        """<summary>프레임 시간을 최근 통계에 반영한다.</summary><input>호출 인수 또는 공유 상태</input><output>처리 결과 또는 상태 갱신</output><reason>수업의 처리 흐름을 코드와 함께 설명하기 위해서다.</reason>"""
        with self.lock:
            self.history.append(dict(times=self.current.copy(),elapsed=max(perf_counter()-self.started,1e-9)))
            self.counters["frames"]+=1
            self.last_skipped=self.skipped
            self.active="idle"

    def abort_frame(self,error):
        """<summary>실패한 프레임을 중단하고 경고를 남긴다.</summary><param name="error">error 인수</param><input>호출 인수 또는 공유 상태</input><output>처리 결과 또는 상태 갱신</output><reason>수업의 처리 흐름을 코드와 함께 설명하기 위해서다.</reason>"""
        with self.lock:
            self.counters["aborted"]+=1
            self.active="idle"
            self.current={}
            self.log("WARN",str(error))

    def record(self,name,ms):
        """<summary>동일 단계의 시간을 합산한다.</summary><param name="name">name 인수</param><param name="ms">ms 인수</param><input>호출 인수 또는 공유 상태</input><output>처리 결과 또는 상태 갱신</output><reason>수업의 처리 흐름을 코드와 함께 설명하기 위해서다.</reason>"""
        if name not in LABELS or not math.isfinite(float(ms)) or ms<0:
            raise ValueError("Invalid timing")
        with self.lock:
            self.current[name]=self.current.get(name,0)+float(ms)

    def increment(self,name,amount=1):
        """<summary>누적 카운터를 갱신한다.</summary><param name="name">name 인수</param><param name="amount">amount 인수</param><input>호출 인수 또는 공유 상태</input><output>처리 결과 또는 상태 갱신</output><reason>수업의 처리 흐름을 코드와 함께 설명하기 위해서다.</reason>"""
        with self.lock:
            self.counters[name]=self.counters.get(name,0)+amount

    def set_status(self,**values):
        """<summary>공유 상태를 갱신한다.</summary><param name="values">values 인수</param><input>호출 인수 또는 공유 상태</input><output>처리 결과 또는 상태 갱신</output><reason>수업의 처리 흐름을 코드와 함께 설명하기 위해서다.</reason>"""
        with self.lock:
            self.status.update(values)

    def log(self,level,message,throttle=False):
        """<summary>필터 규칙에 따라 로그를 링버퍼에 남긴다.</summary><param name="level">level 인수</param><param name="message">message 인수</param><param name="throttle">throttle 인수</param><input>호출 인수 또는 공유 상태</input><output>처리 결과 또는 상태 갱신</output><reason>수업의 처리 흐름을 코드와 함께 설명하기 위해서다.</reason>"""
        with self.lock:
            if (level in ("INFO","DEBUG") or throttle) and self.frame%self.log_every:
                return
            self.seq+=1
            self.events.append(dict(seq=self.seq,frame=self.frame,level=level,message=str(message)))

    def stage(self,name,manual=False):
        """<summary>함수의 설명과 실행 시간을 등록한다.</summary><param name="name">name 인수</param><param name="manual">manual 인수</param><input>호출 인수 또는 공유 상태</input><output>처리 결과 또는 상태 갱신</output><reason>수업의 처리 흐름을 코드와 함께 설명하기 위해서다.</reason>"""
        def decorate(function):
            """<summary>함수를 계측 래퍼로 감싼다.</summary><param name="function">function 인수</param><input>호출 인수 또는 공유 상태</input><output>처리 결과 또는 상태 갱신</output><reason>수업의 처리 흐름을 코드와 함께 설명하기 위해서다.</reason>"""
            try:
                meta=parse_xml_docstring(function)
            except ET.ParseError as error:
                meta=dict(error=str(error))
                logging.warning("XML parse failed for %s: %s",name,error)
            with self.lock:
                self.registry[name]=dict(id=name,label=LABELS[name],function=function.__name__,**meta)
            @wraps(function)
            def wrapped(*args,**kwargs):
                """<summary>실제 함수를 실행하고 입출력 요약을 남긴다.</summary><param name="args">args 인수</param><param name="kwargs">kwargs 인수</param><input>호출 인수 또는 공유 상태</input><output>처리 결과 또는 상태 갱신</output><reason>수업의 처리 흐름을 코드와 함께 설명하기 위해서다.</reason>"""
                with self.lock:
                    self.active=name
                start=perf_counter()
                result=function(*args,**kwargs)
                elapsed=(perf_counter()-start)*1000
                if not manual:
                    self.record(name,elapsed)
                self.log("INFO",f"#{self.frame:04d} | {name} | {elapsed:.2f}ms")
                self.log("DEBUG",f"{name} in={describe(args[-1] if args else None)} out={describe(result)}")
                return result
            return wrapped
        return decorate

    def metadata(self):
        """<summary>등록한 함수 설명을 복사한다.</summary><input>호출 인수 또는 공유 상태</input><output>처리 결과 또는 상태 갱신</output><reason>수업의 처리 흐름을 코드와 함께 설명하기 위해서다.</reason>"""
        with self.lock:
            return [dict(id=name,label=label,**{k:v for k,v in self.registry.get(name,{}).items() if k not in ("id","label")}) for name,label in LABELS.items()]

    def snapshot(self,after_seq=0):
        """<summary>공유 상태의 일관된 사본을 반환한다.</summary><param name="after_seq">after_seq 인수</param><input>호출 인수 또는 공유 상태</input><output>처리 결과 또는 상태 갱신</output><reason>수업의 처리 흐름을 코드와 함께 설명하기 위해서다.</reason>"""
        with self.lock:
            samples=list(self.history)
            means={name:sum(s["times"].get(name,0) for s in samples)/max(len(samples),1) for name in LABELS}
            total=sum(means.values())
            stages=[]
            for meta in self.metadata():
                name=meta["id"]
                executed=[s["times"][name] for s in samples if name in s["times"]]
                stages.append(dict(**meta,avg_ms=round(means[name],3),execution_avg_ms=round(sum(executed)/max(len(executed),1),3),share=round(means[name]/total if total else 0,4)))
            logs=[e.copy() for e in self.events if e["seq"]>after_seq][:config.SSE_MAX_LOGS]
            return dict(stages=stages,frame=self.frame,active=self.active,skipped=self.last_skipped,fps=round(len(samples)/sum(s["elapsed"] for s in samples),2) if samples else 0,bottleneck=max(means,key=means.get) if total else None,counters=self.counters.copy(),status=self.status.copy(),logs=logs,next_seq=logs[-1]["seq"] if logs else after_seq,log_gap=bool(self.events and after_seq and after_seq<self.events[0]["seq"]-1))


PIPELINE=Pipeline()
stage=PIPELINE.stage
