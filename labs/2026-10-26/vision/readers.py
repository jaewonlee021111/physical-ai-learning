"""하나의 입력 리더가 최신 프레임만 공유한다."""
from pathlib import Path
import sys
import threading
from time import perf_counter
from urllib.request import urlopen
from urllib.parse import urlsplit
import cv2
import numpy as np
import config
from pipeline import PIPELINE

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"2026-10-23"/"gateway"))
from remote import jpeg_packets


class LatestReader:
    """<summary>LatestReader의 상태와 동작을 관리한다.</summary><input>호출 인수 또는 공유 상태</input><output>처리 결과 또는 상태 갱신</output><reason>수업의 처리 흐름을 코드와 함께 설명하기 위해서다.</reason>"""
    def __init__(self):
        """<summary>인스턴스 설정과 동기화 자원을 준비한다.</summary><input>호출 인수 또는 공유 상태</input><output>처리 결과 또는 상태 갱신</output><reason>수업의 처리 흐름을 코드와 함께 설명하기 위해서다.</reason>"""
        self.condition=threading.Condition()
        self.stop=threading.Event()
        self.latest=None
        self.thread=None
        self.count=0
        self.bytes=0
        self.metrics_at=perf_counter()

    def publish(self,value):
        """<summary>최신 입력 한 장으로 교체하고 누락 수를 센다.</summary><param name="value">value 인수</param><input>호출 인수 또는 공유 상태</input><output>처리 결과 또는 상태 갱신</output><reason>수업의 처리 흐름을 코드와 함께 설명하기 위해서다.</reason>"""
        with self.condition:
            if self.latest is not None:
                PIPELINE.increment("dropped")
            self.latest=(value,perf_counter())
            self.count+=1
            self.bytes+=len(value) if isinstance(value,bytes) else value.nbytes
            elapsed=perf_counter()-self.metrics_at
            if elapsed>=1:
                PIPELINE.set_status(rx_fps=round(self.count/elapsed,2),kbps=round(self.bytes*8/elapsed/1000,2))
                self.count=self.bytes=0
                self.metrics_at=perf_counter()
            self.condition.notify_all()

    def take(self,timeout=2):
        """<summary>새 입력을 기다려 한 번만 소비한다.</summary><param name="timeout">timeout 인수</param><input>호출 인수 또는 공유 상태</input><output>처리 결과 또는 상태 갱신</output><reason>수업의 처리 흐름을 코드와 함께 설명하기 위해서다.</reason>"""
        with self.condition:
            self.condition.wait_for(lambda:self.latest is not None or self.stop.is_set(),timeout)
            if self.latest is None:
                raise TimeoutError("No frame received")
            result=self.latest
            self.latest=None
            return result

    def start(self):
        """<summary>입력과 처리 스레드를 시작한다.</summary><input>호출 인수 또는 공유 상태</input><output>처리 결과 또는 상태 갱신</output><reason>수업의 처리 흐름을 코드와 함께 설명하기 위해서다.</reason>"""
        self.thread=threading.Thread(target=self.run,daemon=True)
        self.thread.start()

    def close(self):
        """<summary>중단을 알리고 스레드와 자원을 정리한다.</summary><input>호출 인수 또는 공유 상태</input><output>처리 결과 또는 상태 갱신</output><reason>수업의 처리 흐름을 코드와 함께 설명하기 위해서다.</reason>"""
        self.stop.set()
        with self.condition:
            self.condition.notify_all()
        if self.thread:
            self.thread.join(timeout=config.STREAM_TIMEOUT_SEC+2)


class MjpegStreamReader(LatestReader):
    """<summary>MjpegStreamReader의 상태와 동작을 관리한다.</summary><input>호출 인수 또는 공유 상태</input><output>처리 결과 또는 상태 갱신</output><reason>수업의 처리 흐름을 코드와 함께 설명하기 위해서다.</reason>"""
    def __init__(self,url):
        """<summary>인스턴스 설정과 동기화 자원을 준비한다.</summary><param name="url">url 인수</param><input>호출 인수 또는 공유 상태</input><output>처리 결과 또는 상태 갱신</output><reason>수업의 처리 흐름을 코드와 함께 설명하기 위해서다.</reason>"""
        super().__init__()
        parsed=urlsplit(url)
        if parsed.scheme not in ("http","https") or not parsed.hostname or parsed.username or parsed.password:
            raise ValueError("HTTP(S) camera URL without credentials required")
        self.url=url

    def run(self):
        """<summary>중단 요청까지 입력 또는 처리를 반복한다.</summary><input>호출 인수 또는 공유 상태</input><output>처리 결과 또는 상태 갱신</output><reason>수업의 처리 흐름을 코드와 함께 설명하기 위해서다.</reason>"""
        while not self.stop.is_set():
            try:
                PIPELINE.set_status(connected=False)
                with urlopen(self.url,timeout=config.STREAM_TIMEOUT_SEC) as response:
                    PIPELINE.set_status(connected=True)
                    for jpeg in jpeg_packets(response):
                        if self.stop.is_set():
                            break
                        self.publish(jpeg)
                if not self.stop.is_set():
                    raise ConnectionError("Camera stream ended")
            except Exception as error:
                PIPELINE.set_status(connected=False,rx_fps=0,kbps=0)
                PIPELINE.increment("reconnects")
                PIPELINE.log("WARN",f"Camera disconnected: {type(error).__name__}")
                self.stop.wait(config.RECONNECT_DELAY_SEC)
        PIPELINE.set_status(connected=False)


class WebcamReader(LatestReader):
    """<summary>WebcamReader의 상태와 동작을 관리한다.</summary><input>호출 인수 또는 공유 상태</input><output>처리 결과 또는 상태 갱신</output><reason>수업의 처리 흐름을 코드와 함께 설명하기 위해서다.</reason>"""
    def __init__(self,index=0):
        """<summary>인스턴스 설정과 동기화 자원을 준비한다.</summary><param name="index">index 인수</param><input>호출 인수 또는 공유 상태</input><output>처리 결과 또는 상태 갱신</output><reason>수업의 처리 흐름을 코드와 함께 설명하기 위해서다.</reason>"""
        super().__init__()
        self.index=index

    def run(self):
        """<summary>중단 요청까지 입력 또는 처리를 반복한다.</summary><input>호출 인수 또는 공유 상태</input><output>처리 결과 또는 상태 갱신</output><reason>수업의 처리 흐름을 코드와 함께 설명하기 위해서다.</reason>"""
        cap=cv2.VideoCapture(self.index)
        try:
            while not self.stop.is_set():
                ok,frame=cap.read()
                if not ok:
                    PIPELINE.set_status(connected=False)
                    PIPELINE.log("WARN","Webcam unavailable")
                    self.stop.wait(1)
                    cap.release()
                    cap=cv2.VideoCapture(self.index)
                    continue
                PIPELINE.set_status(connected=True)
                self.publish(frame)
        finally:
            cap.release()
            PIPELINE.set_status(connected=False)


class SyntheticReader(LatestReader):
    """<summary>SyntheticReader의 상태와 동작을 관리한다.</summary><input>호출 인수 또는 공유 상태</input><output>처리 결과 또는 상태 갱신</output><reason>수업의 처리 흐름을 코드와 함께 설명하기 위해서다.</reason>"""
    def run(self):
        """<summary>중단 요청까지 입력 또는 처리를 반복한다.</summary><input>호출 인수 또는 공유 상태</input><output>처리 결과 또는 상태 갱신</output><reason>수업의 처리 흐름을 코드와 함께 설명하기 위해서다.</reason>"""
        index=0
        PIPELINE.set_status(connected=True,source="synthetic (test only)")
        while not self.stop.is_set():
            frame=np.full((240,320,3),35,dtype=np.uint8)
            cv2.rectangle(frame,(20+index%150,60),(70+index%150,130),(130,155,175),-1)
            cv2.putText(frame,"SYNTHETIC TEST",(20,215),cv2.FONT_HERSHEY_SIMPLEX,.6,(220,220,220),1)
            self.publish(frame)
            index+=1
            self.stop.wait(.05)
