"""ESP32 MJPEG를 읽는 입력 어댑터. 실제 실패를 합성 영상으로 대체하지 않는다."""
from time import sleep
from urllib.parse import urlsplit
from urllib.request import urlopen
import cv2
import numpy as np


def jpeg_packets(stream, limit=4*1024*1024):
    """<summary>분할된 MJPEG 바이트에서 완전한 JPEG를 추출한다.</summary>
    <param name="stream">read1 또는 read를 제공하는 입력</param><param name="limit">최대 버퍼 바이트</param>
    <input>HTTP multipart 스트림</input><output>JPEG 바이트 반복자</output>
    <reason>TCP 조각 경계와 JPEG 프레임 경계는 일치하지 않는다.</reason>"""
    buffer = bytearray()
    read = getattr(stream,"read1",stream.read)
    while True:
        chunk = read(8192)
        if not chunk:
            return
        buffer.extend(chunk)
        while True:
            start = buffer.find(b"\xff\xd8")
            if start < 0:
                if len(buffer)>limit:
                    raise ValueError("MJPEG header exceeded buffer limit")
                break
            if start:
                del buffer[:start]
            end = buffer.find(b"\xff\xd9",2)
            if end < 0:
                if len(buffer)>limit:
                    raise ValueError("JPEG exceeded buffer limit")
                break
            yield bytes(buffer[:end+2])
            del buffer[:end+2]


class RemoteReader:
    """<summary>원격 MJPEG를 기존 카메라 서비스의 read 인터페이스에 맞춘다.</summary>
    <input>명시한 HTTP URL</input><output>OpenCV BGR 프레임</output>
    <reason>10/22 처리·추론·대시보드를 그대로 재사용한다.</reason>"""
    def __init__(self,url,timeout=2):
        """<summary>URL을 검증하고 연결 설정만 보관한다.</summary>
        <param name="url">ESP32의 /stream 주소</param><param name="timeout">초 단위 읽기 제한</param>
        <input>URL</input><output>지연 연결 어댑터</output><reason>실행 전에는 카메라를 점유하지 않는다.</reason>"""
        parsed=urlsplit(url)
        if parsed.scheme not in ("http","https") or not parsed.hostname or parsed.username or parsed.password:
            raise ValueError("Use an explicit HTTP(S) camera URL without embedded credentials")
        self.url,self.timeout=url,timeout
        self.response,self.packets=None,None
        self.closed=False

    def read(self):
        """<summary>JPEG를 복호화하고 끊기면 한 번 재접속한다.</summary>
        <input>원격 스트림</input><output>성공 여부·BGR 배열</output>
        <reason>일시적인 끊김과 영구적인 연결 실패를 구분한다.</reason>"""
        for attempt in range(2):
            if self.closed:
                return False,None
            try:
                if self.response is None:
                    self.response=urlopen(self.url,timeout=self.timeout)
                    self.packets=jpeg_packets(self.response)
                image=cv2.imdecode(np.frombuffer(next(self.packets),dtype=np.uint8),cv2.IMREAD_COLOR)
                if image is None:
                    raise ValueError("Invalid JPEG frame")
                return True,image
            except (OSError,ValueError,StopIteration):
                if self.response is not None:
                    self.response.close()
                self.response,self.packets=None,None
                if attempt==0:
                    sleep(.3)
        return False,None

    def release(self):
        """<summary>입력 연결을 닫는다.</summary><input>어댑터 상태</input><output>닫힌 연결</output>
        <reason>서버 종료 후 ESP32 스트림을 계속 점유하지 않는다.</reason>"""
        self.closed=True
        if self.response is not None:
            self.response.close()
            self.response=None
