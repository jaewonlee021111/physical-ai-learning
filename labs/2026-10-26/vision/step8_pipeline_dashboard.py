"""ESP32 MJPEG → 최신 프레임 → 계측 파이프라인 → Flask 대시보드."""
import argparse
from collections import deque
from dataclasses import dataclass
import json
import math
from pathlib import Path
import threading
from time import perf_counter
import uuid
import cv2
import numpy as np
from flask import Flask,Response,jsonify,render_template,request,send_from_directory
import config
from pipeline import PIPELINE,stage
from readers import MjpegStreamReader,WebcamReader,SyntheticReader


class RuntimeSettings:
    """<summary>RuntimeSettings의 상태와 동작을 관리한다.</summary><input>호출 인수 또는 공유 상태</input><output>처리 결과 또는 상태 갱신</output><reason>수업의 처리 흐름을 코드와 함께 설명하기 위해서다.</reason>"""
    def __init__(self,skip=config.SKIP,imgsz=config.IMG_SIZE,conf=config.CONF):
        """<summary>인스턴스 설정과 동기화 자원을 준비한다.</summary><param name="skip">skip 인수</param><param name="imgsz">imgsz 인수</param><param name="conf">conf 인수</param><input>호출 인수 또는 공유 상태</input><output>처리 결과 또는 상태 갱신</output><reason>수업의 처리 흐름을 코드와 함께 설명하기 위해서다.</reason>"""
        self.lock=threading.Lock()
        self.values={}
        self.update(dict(skip=skip,imgsz=imgsz,conf=conf))

    def update(self,data):
        """<summary>설정 값의 범위를 검증하고 적용한다.</summary><param name="data">data 인수</param><input>호출 인수 또는 공유 상태</input><output>처리 결과 또는 상태 갱신</output><reason>수업의 처리 흐름을 코드와 함께 설명하기 위해서다.</reason>"""
        if not isinstance(data,dict) or set(data)-{"skip","imgsz","conf"}:
            raise ValueError("Settings object: skip, imgsz, conf only")
        with self.lock:
            values={**self.values,**data}
            skip,imgsz,conf=values.get("skip"),values.get("imgsz"),values.get("conf")
            if type(skip) is not int or not 1<=skip<=30:
                raise ValueError("skip: integer 1..30")
            if type(imgsz) is not int or not 160<=imgsz<=1280 or imgsz%32:
                raise ValueError("imgsz: multiple of 32, 160..1280")
            if type(conf) not in (int,float) or not math.isfinite(conf) or not 0<=conf<=1:
                raise ValueError("conf: finite number 0..1")
            self.values=dict(skip=skip,imgsz=imgsz,conf=float(conf))
            return self.values.copy()

    def snapshot(self):
        """<summary>공유 상태의 일관된 사본을 반환한다.</summary><input>호출 인수 또는 공유 상태</input><output>처리 결과 또는 상태 갱신</output><reason>수업의 처리 흐름을 코드와 함께 설명하기 위해서다.</reason>"""
        with self.lock:
            return self.values.copy()


@dataclass
class Detection:
    """<summary>Detection의 상태와 동작을 관리한다.</summary><input>호출 인수 또는 공유 상태</input><output>처리 결과 또는 상태 갱신</output><reason>수업의 처리 흐름을 코드와 함께 설명하기 위해서다.</reason>"""
    xyxy:list
    label:str
    confidence:float


class Detector:
    """<summary>Detector의 상태와 동작을 관리한다.</summary><input>호출 인수 또는 공유 상태</input><output>처리 결과 또는 상태 갱신</output><reason>수업의 처리 흐름을 코드와 함께 설명하기 위해서다.</reason>"""
    def __init__(self,model=config.MODEL_PATH,device=config.DEVICE,classes=None):
        """<summary>인스턴스 설정과 동기화 자원을 준비한다.</summary><param name="model">model 인수</param><param name="device">device 인수</param><param name="classes">classes 인수</param><input>호출 인수 또는 공유 상태</input><output>처리 결과 또는 상태 갱신</output><reason>수업의 처리 흐름을 코드와 함께 설명하기 위해서다.</reason>"""
        import torch
        from ultralytics import YOLO
        self.device=device
        self.classes=set(classes or [])
        if (device.startswith("cuda") and not torch.cuda.is_available()) or (device=="mps" and not torch.backends.mps.is_available()):
            PIPELINE.log("WARN",f"{device} unavailable: CPU fallback")
            self.device="cpu"
        try:
            self.model=YOLO(model)
            self.path=model
        except Exception:
            PIPELINE.log("WARN","Primary model unavailable: fallback model requested")
            self.model=YOLO(config.FALLBACK_MODEL_PATH)
            self.path=config.FALLBACK_MODEL_PATH
        self.predict(np.zeros((320,320,3),dtype=np.uint8),dict(imgsz=320,conf=.4))

    def predict(self,frame,settings):
        """<summary>준비된 모델로 실제 추론을 수행한다.</summary><param name="frame">frame 인수</param><param name="settings">settings 인수</param><input>호출 인수 또는 공유 상태</input><output>처리 결과 또는 상태 갱신</output><reason>수업의 처리 흐름을 코드와 함께 설명하기 위해서다.</reason>"""
        return self.model.predict(frame,imgsz=settings["imgsz"],conf=settings["conf"],device=self.device,half=self.device.startswith("cuda"),verbose=False)[0]


class OutputStore:
    """<summary>OutputStore의 상태와 동작을 관리한다.</summary><input>호출 인수 또는 공유 상태</input><output>처리 결과 또는 상태 갱신</output><reason>수업의 처리 흐름을 코드와 함께 설명하기 위해서다.</reason>"""
    def __init__(self):
        """<summary>인스턴스 설정과 동기화 자원을 준비한다.</summary><input>호출 인수 또는 공유 상태</input><output>처리 결과 또는 상태 갱신</output><reason>수업의 처리 흐름을 코드와 함께 설명하기 위해서다.</reason>"""
        self.condition=threading.Condition()
        self.seq=0
        self.raw=None
        self.detect=None
        self.closed=False

    def put(self,raw,detect):
        """<summary>최신 출력 두 장을 공유한다.</summary><param name="raw">raw 인수</param><param name="detect">detect 인수</param><input>호출 인수 또는 공유 상태</input><output>처리 결과 또는 상태 갱신</output><reason>수업의 처리 흐름을 코드와 함께 설명하기 위해서다.</reason>"""
        with self.condition:
            self.raw,self.detect=raw,detect
            self.seq+=1
            self.condition.notify_all()

    def stream(self,raw=False):
        """<summary>새 JPEG가 생길 때만 응답한다.</summary><param name="raw">raw 인수</param><input>호출 인수 또는 공유 상태</input><output>처리 결과 또는 상태 갱신</output><reason>수업의 처리 흐름을 코드와 함께 설명하기 위해서다.</reason>"""
        last=0
        while True:
            with self.condition:
                self.condition.wait_for(lambda:self.seq!=last or self.closed,2)
                if self.closed:
                    return
                if self.seq==last:
                    continue
                last=self.seq
                jpeg=self.raw if raw else self.detect
            yield b"--frame\r\nContent-Type: image/jpeg\r\nContent-Length: "+str(len(jpeg)).encode()+b"\r\n\r\n"+jpeg+b"\r\n"

    def close(self):
        """<summary>중단을 알리고 스레드와 자원을 정리한다.</summary><input>호출 인수 또는 공유 상태</input><output>처리 결과 또는 상태 갱신</output><reason>수업의 처리 흐름을 코드와 함께 설명하기 위해서다.</reason>"""
        with self.condition:
            self.closed=True
            self.condition.notify_all()


@stage("capture")
def capture_frame(reader):
    """<summary>최신 입력을 기다려 JPEG를 디코딩한다.</summary><param name="reader">입력 리더</param><input>최신 JPEG 또는 BGR</input><output>BGR 이미지</output><reason>네트워크 대기와 디코딩 시간을 입력 단계에 포함해 계측한다.</reason>"""
    start=perf_counter()
    value,received=reader.take()
    waited=(perf_counter()-start)*1000
    decode_at=perf_counter()
    frame=cv2.imdecode(np.frombuffer(value,np.uint8),cv2.IMREAD_COLOR) if isinstance(value,bytes) else value
    if frame is None:
        raise ValueError("JPEG decode failed")
    PIPELINE.set_status(wait_ms=round(waited,3),decode_ms=round((perf_counter()-decode_at)*1000,3),age_ms=round((perf_counter()-received)*1000,3))
    return frame


@stage("preprocess")
def preprocess(frame):
    """<summary>BGR uint8 형식과 최대 폭을 맞춘다.</summary><param name="frame">입력 이미지</param><input>이미지 배열</input><output>BGR 이미지</output><reason>영상 크기로 인한 추가 전송과 그리기 비용을 제한한다.</reason>"""
    if frame.ndim==2:
        frame=cv2.cvtColor(frame,cv2.COLOR_GRAY2BGR)
    if frame.dtype!=np.uint8:
        frame=np.clip(frame,0,255).astype(np.uint8)
    if frame.shape[1]>960:
        frame=cv2.resize(frame,(960,round(frame.shape[0]*960/frame.shape[1])))
    return np.ascontiguousarray(frame)


@stage("inference",manual=True)
def run_inference(detector,frame,settings,frame_number):
    """<summary>지정된 간격으로만 모델을 실행한다.</summary><param name="detector">YOLO 어댑터 또는 비활성</param><param name="frame">BGR 이미지</param><param name="settings">실행 설정</param><param name="frame_number">프레임 번호</param><input>이미지와 설정</input><output>Results 또는 생략</output><reason>전송과 추론의 부하를 구분하고 모델 내부 세 단계 시간을 이중 계산하지 않는다.</reason>"""
    if detector is None or (frame_number-1)%settings["skip"]:
        with PIPELINE.lock:
            PIPELINE.skipped=True
        PIPELINE.log("WARN","Inference skipped (disabled or interval)",throttle=True)
        return None
    start=perf_counter()
    result=detector.predict(frame,settings)
    wall_ms=(perf_counter()-start)*1000
    speeds=getattr(result,"speed",{})
    for name in ("preprocess","inference","postprocess"):
        PIPELINE.record(name,float(speeds.get(name,wall_ms if name=="inference" else 0) or 0))
    PIPELINE.set_status(inference_wall_ms=round(wall_ms,3))
    return result


@stage("postprocess")
def postprocess(result,previous,classes):
    """<summary>검출 결과를 가벼운 Detection 목록으로 변환한다.</summary><param name="result">추론 결과 또는 생략</param><param name="previous">이전 검출</param><param name="classes">허용할 클래스 이름</param><input>모델 결과</input><output>박스·라벨·신뢰도</output><reason>추론 생략 시 이전 검출을 재사용하고 새 추론과 구분한다.</reason>"""
    if result is None:
        return previous
    detections=[]
    for box in result.boxes:
        label=result.names[int(box.cls.item())]
        if not classes or label in classes:
            detections.append(Detection(box.xyxy[0].cpu().tolist(),label,float(box.conf.item())))
    return detections


@stage("visualize")
def visualize(frame,detections):
    """<summary>한 가지 강조색으로 검출과 FPS를 그린다.</summary><param name="frame">원본 이미지</param><param name="detections">검출 목록</param><input>BGR 이미지와 박스</input><output>그리기 결과</output><reason>원본을 수정하지 않아 가공 전후를 비교할 수 있다.</reason>"""
    image=frame.copy()
    for detection in detections:
        x1,y1,x2,y2=map(int,detection.xyxy)
        cv2.rectangle(image,(x1,y1),(x2,y2),(130,155,175),2)
        cv2.putText(image,f"{detection.label} {detection.confidence:.2f}",(x1,max(15,y1-5)),cv2.FONT_HERSHEY_SIMPLEX,.5,(130,155,175),1)
    snapshot=PIPELINE.snapshot()
    cv2.putText(image,f"FPS {snapshot['fps']:.1f} | {'CACHED' if PIPELINE.skipped else 'INFERRED'}",(12,22),cv2.FONT_HERSHEY_SIMPLEX,.5,(220,220,220),1)
    return image


@stage("output")
def output(store,raw,annotated):
    """<summary>원본과 그린 영상을 JPEG로 공유한다.</summary><param name="store">출력 저장소</param><param name="raw">원본</param><param name="annotated">그리기 결과</param><input>두 이미지</input><output>최신 JPEG</output><reason>브라우저마다 재추론하거나 재인코딩하지 않는다.</reason>"""
    ok1,first=cv2.imencode('.jpg',raw,[cv2.IMWRITE_JPEG_QUALITY,config.JPEG_QUALITY])
    ok2,second=cv2.imencode('.jpg',annotated,[cv2.IMWRITE_JPEG_QUALITY,config.JPEG_QUALITY])
    if not ok1 or not ok2:
        raise RuntimeError("JPEG encoding failed")
    store.put(first.tobytes(),second.tobytes())


class Processor:
    """<summary>Processor의 상태와 동작을 관리한다.</summary><input>호출 인수 또는 공유 상태</input><output>처리 결과 또는 상태 갱신</output><reason>수업의 처리 흐름을 코드와 함께 설명하기 위해서다.</reason>"""
    def __init__(self,reader,settings,detector=None):
        """<summary>인스턴스 설정과 동기화 자원을 준비한다.</summary><param name="reader">reader 인수</param><param name="settings">settings 인수</param><param name="detector">detector 인수</param><input>호출 인수 또는 공유 상태</input><output>처리 결과 또는 상태 갱신</output><reason>수업의 처리 흐름을 코드와 함께 설명하기 위해서다.</reason>"""
        self.reader,self.settings,self.detector=reader,settings,detector
        self.store=OutputStore()
        self.stop=threading.Event()
        self.thread=None

    def start(self):
        """<summary>입력과 처리 스레드를 시작한다.</summary><input>호출 인수 또는 공유 상태</input><output>처리 결과 또는 상태 갱신</output><reason>수업의 처리 흐름을 코드와 함께 설명하기 위해서다.</reason>"""
        self.reader.start()
        self.thread=threading.Thread(target=self.run,daemon=True)
        self.thread.start()

    def run(self):
        """<summary>중단 요청까지 입력 또는 처리를 반복한다.</summary><input>호출 인수 또는 공유 상태</input><output>처리 결과 또는 상태 갱신</output><reason>수업의 처리 흐름을 코드와 함께 설명하기 위해서다.</reason>"""
        previous=[]
        while not self.stop.is_set():
            PIPELINE.begin_frame()
            try:
                frame=preprocess(capture_frame(self.reader))
                settings=self.settings.snapshot()
                result=run_inference(self.detector,frame,settings,PIPELINE.frame)
                previous=postprocess(result,previous,getattr(self.detector,"classes",set()))
                output(self.store,frame,visualize(frame,previous))
                PIPELINE.end_frame()
            except Exception as error:
                PIPELINE.abort_frame(error)
                self.stop.wait(.1)

    def close(self):
        """<summary>중단을 알리고 스레드와 자원을 정리한다.</summary><input>호출 인수 또는 공유 상태</input><output>처리 결과 또는 상태 갱신</output><reason>수업의 처리 흐름을 코드와 함께 설명하기 위해서다.</reason>"""
        self.stop.set()
        self.reader.close()
        if self.thread:
            self.thread.join(timeout=4)
        self.store.close()


def create_app(processor,capture_dir=None):
    """<summary>실습용 HTTP 라우트를 등록한다.</summary><param name="processor">processor 인수</param><param name="capture_dir">capture_dir 인수</param><input>호출 인수 또는 공유 상태</input><output>처리 결과 또는 상태 갱신</output><reason>수업의 처리 흐름을 코드와 함께 설명하기 위해서다.</reason>"""
    app=Flask(__name__)
    directory=Path(capture_dir or config.CAPTURE_DIR)
    directory.mkdir(parents=True,exist_ok=True)

    @app.get('/')
    def index():
        """<summary>대시보드 HTML을 제공한다.</summary><input>호출 인수 또는 공유 상태</input><output>처리 결과 또는 상태 갱신</output><reason>수업의 처리 흐름을 코드와 함께 설명하기 위해서다.</reason>"""
        return render_template('dashboard.html')

    @app.get('/detect_feed')
    def detect_feed():
        """<summary>검출 영상 스트림을 제공한다.</summary><input>호출 인수 또는 공유 상태</input><output>처리 결과 또는 상태 갱신</output><reason>수업의 처리 흐름을 코드와 함께 설명하기 위해서다.</reason>"""
        return Response(processor.store.stream(),mimetype='multipart/x-mixed-replace; boundary=frame')

    @app.get('/raw_feed')
    def raw_feed():
        """<summary>원본 영상 스트림을 제공한다.</summary><input>호출 인수 또는 공유 상태</input><output>처리 결과 또는 상태 갱신</output><reason>수업의 처리 흐름을 코드와 함께 설명하기 위해서다.</reason>"""
        return Response(processor.store.stream(raw=True),mimetype='multipart/x-mixed-replace; boundary=frame')

    @app.get('/api/pipeline')
    def pipeline_snapshot():
        """<summary>계측 스냅샷을 JSON으로 제공한다.</summary><input>호출 인수 또는 공유 상태</input><output>처리 결과 또는 상태 갱신</output><reason>수업의 처리 흐름을 코드와 함께 설명하기 위해서다.</reason>"""
        return jsonify(PIPELINE.snapshot())

    @app.get('/api/config')
    def current_config():
        """<summary>현재 설정과 소스 상태를 제공한다.</summary><input>호출 인수 또는 공유 상태</input><output>처리 결과 또는 상태 갱신</output><reason>수업의 처리 흐름을 코드와 함께 설명하기 위해서다.</reason>"""
        return jsonify(**processor.settings.snapshot(),**PIPELINE.snapshot()['status'])

    @app.post('/api/settings')
    def settings():
        """<summary>변경 요청을 검증하고 적용한다.</summary><input>호출 인수 또는 공유 상태</input><output>처리 결과 또는 상태 갱신</output><reason>수업의 처리 흐름을 코드와 함께 설명하기 위해서다.</reason>"""
        try:
            return jsonify(processor.settings.update(request.get_json(silent=True)))
        except (ValueError,TypeError):
            return jsonify(error='skip 1..30, imgsz multiple of 32 in 160..1280, conf 0..1'),400

    @app.get('/events')
    def events():
        """<summary>접속별 로그 커서로 SSE를 제공한다.</summary><input>호출 인수 또는 공유 상태</input><output>처리 결과 또는 상태 갱신</output><reason>수업의 처리 흐름을 코드와 함께 설명하기 위해서다.</reason>"""
        def generate():
            """<summary>새 로그와 통계를 주기적으로 보낸다.</summary><input>호출 인수 또는 공유 상태</input><output>처리 결과 또는 상태 갱신</output><reason>수업의 처리 흐름을 코드와 함께 설명하기 위해서다.</reason>"""
            cursor=0
            while not processor.stop.is_set():
                snapshot=PIPELINE.snapshot(cursor)
                cursor=snapshot['next_seq']
                yield 'data: '+json.dumps(snapshot,ensure_ascii=False)+'\n\n'
                processor.stop.wait(config.SSE_INTERVAL_SEC)
        return Response(generate(),mimetype='text/event-stream',headers={'Cache-Control':'no-cache','X-Accel-Buffering':'no'})

    @app.post('/capture')
    def capture():
        """<summary>현재 출력 JPEG 한 장을 저장한다.</summary><input>호출 인수 또는 공유 상태</input><output>처리 결과 또는 상태 갱신</output><reason>수업의 처리 흐름을 코드와 함께 설명하기 위해서다.</reason>"""
        with processor.store.condition:
            jpeg=processor.store.detect
        if jpeg is None:
            return jsonify(error='No frame yet'),503
        name=f'{uuid.uuid4().hex}.jpg'
        (directory/name).write_bytes(jpeg)
        return jsonify(name=name,url='/captures/'+name)

    @app.get('/api/captures')
    def captures():
        """<summary>최근 촬영 파일 목록을 제공한다.</summary><input>호출 인수 또는 공유 상태</input><output>처리 결과 또는 상태 갱신</output><reason>수업의 처리 흐름을 코드와 함께 설명하기 위해서다.</reason>"""
        return jsonify([dict(name=p.name,url='/captures/'+p.name) for p in sorted(directory.glob('*.jpg'),key=lambda x:x.stat().st_mtime,reverse=True)[:10]])

    @app.get('/captures/<path:name>')
    def capture_file(name):
        """<summary>지정 폴더 내부의 촬영 파일만 제공한다.</summary><param name="name">name 인수</param><input>호출 인수 또는 공유 상태</input><output>처리 결과 또는 상태 갱신</output><reason>수업의 처리 흐름을 코드와 함께 설명하기 위해서다.</reason>"""
        return send_from_directory(directory.resolve(),name)

    return app


def main():
    """<summary>명령행 설정을 읽고 실습 서버를 실행한다.</summary><input>호출 인수 또는 공유 상태</input><output>처리 결과 또는 상태 갱신</output><reason>수업의 처리 흐름을 코드와 함께 설명하기 위해서다.</reason>"""
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',choices=['esp32','webcam','synthetic'],default=config.SOURCE)
    parser.add_argument('--url',default=config.CAMERA_URL)
    parser.add_argument('--webcam-index',type=int,default=config.WEBCAM_INDEX)
    parser.add_argument('--device',default=config.DEVICE)
    parser.add_argument('--imgsz',type=int,default=config.IMG_SIZE)
    parser.add_argument('--conf',type=float,default=config.CONF)
    parser.add_argument('--skip',type=int,default=config.SKIP)
    parser.add_argument('--model',default=config.MODEL_PATH)
    parser.add_argument('--no-yolo',action='store_true')
    parser.add_argument('--classes',nargs='*')
    parser.add_argument('--host',default=config.HOST)
    parser.add_argument('--port',type=int,default=config.PORT)
    parser.add_argument('--log-every',type=int,default=config.LOG_EVERY)
    args=parser.parse_args()
    PIPELINE.log_every=max(1,args.log_every)
    settings=RuntimeSettings(args.skip,args.imgsz,args.conf)
    detector=None if args.no_yolo else Detector(args.model,args.device,args.classes)
    PIPELINE.set_status(source=args.source,device=getattr(detector,'device','none'),model=getattr(detector,'path','disabled'),connected=False)
    reader=MjpegStreamReader(args.url) if args.source=='esp32' else WebcamReader(args.webcam_index) if args.source=='webcam' else SyntheticReader()
    processor=Processor(reader,settings,detector)
    processor.start()
    try:
        create_app(processor).run(host=args.host,port=args.port,threaded=True,use_reloader=False)
    finally:
        processor.close()


if __name__=='__main__':
    main()
