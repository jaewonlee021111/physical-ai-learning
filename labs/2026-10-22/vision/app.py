"""Local-only webcam dashboard. One producer owns the camera for all browsers."""
import argparse
from collections import deque
from datetime import datetime, timezone
import json
from pathlib import Path
import threading
from time import perf_counter
import uuid
import stages
import cv2
from flask import Flask, Response, jsonify, render_template, request, send_from_directory
from pipeline import MODES, YoloDetector, process, synthetic_frame


@stages.stage("capture")
def capture_frame(cap, tick):
    """<summary>선택한 카메라 또는 명시적 합성 입력에서 한 장을 받는다.</summary>
    <param name="cap">VideoCapture 또는 없음</param><param name="tick">프레임 순번</param>
    <input>입력 장치</input><output>BGR uint8 배열</output>
    <reason>카메라는 서버 요청마다 열지 않고 한 생산자만 소유한다.</reason>"""
    if cap is None:
        return synthetic_frame(tick * 4)
    ok, frame = cap.read()
    if not ok or frame is None:
        raise RuntimeError("Camera frame read failed")
    return frame


class CameraService:
    """<summary>입력 프레임을 한 스레드에서 처리한다.</summary>
    <input>호출 인수 또는 서비스 상태</input><output>처리 결과 또는 상태 갱신</output>
    <reason>요청마다 카메라를 열면 장치 충돌이 나므로 한 생산자와 최신 프레임 한 장을 공유한다.</reason>"""
    def __init__(self, source="synthetic", camera=0, detector=None, runtime=Path("runtime"), reader=None):
        """<summary>입력·저장·동기화 상태를 준비한다.</summary><param name="source">source 인수</param><param name="camera">camera 인수</param><param name="detector">detector 인수</param><param name="runtime">runtime 인수</param>
        <input>호출 인수 또는 서비스 상태</input><output>처리 결과 또는 상태 갱신</output>
        <reason>실행 전에는 카메라를 열지 않아 테스트와 설정을 독립적으로 할 수 있다.</reason>"""
        self.source, self.camera, self.detector = source, camera, detector
        self.reader = reader
        self.runtime = Path(runtime)
        self.runtime.mkdir(parents=True, exist_ok=True)
        (self.runtime / "captures").mkdir(exist_ok=True)
        self.condition = threading.Condition()
        self.stop_event = threading.Event()
        self.mode, self.confidence, self.infer_every = "original", .5, 3
        self.sequence, self.latest, self.status = 0, None, {}
        self.logs = deque(maxlen=80)
        self.thread = None
        self.error = None
        self.samples = deque(maxlen=30)
        self.cached_objects = []

    def log(self, event):
        """<summary>시간과 함께 이벤트를 메모리와 JSONL에 저장한다.</summary><param name="event">event 인수</param>
        <input>호출 인수 또는 서비스 상태</input><output>처리 결과 또는 상태 갱신</output>
        <reason>오류가 발생한 처리 순서를 재구성하기 위해서다.</reason>"""
        row = {"time": datetime.now(timezone.utc).isoformat(), **event}
        self.logs.append(row)
        with (self.runtime / "events.jsonl").open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    def start(self):
        """<summary>입력 생산자 스레드를 시작한다.</summary>
        <input>호출 인수 또는 서비스 상태</input><output>처리 결과 또는 상태 갱신</output>
        <reason>웹 요청이 카메라 읽기를 직접 기다리지 않게 한다.</reason>"""
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def _run(self):
        """<summary>입력·전처리·추론·출력을 반복한다.</summary>
        <input>호출 인수 또는 서비스 상태</input><output>처리 결과 또는 상태 갱신</output>
        <reason>카메라 소유권과 모델 실행을 한 스레드에 모은다.</reason>"""
        cap = self.reader
        try:
            if self.source == "remote" and cap is None:
                raise RuntimeError("Remote source requires a reader")
            if self.source == "camera":
                cap = cv2.VideoCapture(self.camera)
                if not cap.isOpened():
                    raise RuntimeError(f"Camera {self.camera} unavailable: check USB, permissions, and Zoom camera use")
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 360)
            tick = 0
            while not self.stop_event.is_set():
                stages.FRAME.set(tick + 1)
                start = perf_counter()
                frame = capture_frame(cap, tick)
                capture_ms = (perf_counter() - start) * 1000
                with self.condition:
                    mode, conf, every = self.mode, self.confidence, self.infer_every
                # Sample inference; skipped frames never pretend to have a new prediction.
                detector = self.detector if tick % every == 0 else None
                jpeg, info = process(frame, mode, detector, conf, self.cached_objects if self.detector else None)
                if detector is not None:
                    self.cached_objects = info["detections"]
                info["timings_ms"]["capture"] = round(capture_ms, 3)
                elapsed = perf_counter() - start
                info.update(source=self.source, frame=tick + 1, model_enabled=self.detector is not None,
                            sampled_out=self.detector is not None and detector is None,
                            processing_fps=round(1 / max(elapsed, 1e-9), 2),
                            stream_fps_estimate=round(1 / max(elapsed, .1), 2),
                            bottleneck=max(info["timings_ms"], key=info["timings_ms"].get))
                info.update(device=getattr(self.detector, "device", "cpu"),
                            imgsz=getattr(self.detector, "size", None), conf=conf, skip=every,
                            counts={label: sum(o["label"] == label for o in info["detections"])
                                    for label in {o["label"] for o in info["detections"]}})
                with self.condition:
                    self.samples.append(info["timings_ms"])
                    info["mean_ms"] = {key: round(sum(row.get(key, 0) for row in self.samples)/len(self.samples), 3)
                                       for key in info["timings_ms"]}
                    self.latest, self.status = jpeg, info
                    self.sequence += 1
                    if detector is not None or tick % 10 == 0:
                        self.log({"event": "frame", "level": "INFO", **info})
                    if info["sampled_out"]:
                        self.log({"event": "skip", "level": "WARN", "frame": tick + 1})
                    if tick % 10 == 0:
                        with stages.LOCK:
                            self.log({"event": "stages", "level": "DEBUG", "frame": tick + 1,
                                      "stages": list(stages.EVENTS)[-8:]})
                    self.condition.notify_all()
                tick += 1
                self.stop_event.wait(max(0, .1 - elapsed))
        except Exception as exc:
            with self.condition:
                self.error = str(exc)
                self.log({"event": "error", "message": self.error})
                self.condition.notify_all()
        finally:
            if cap is not None:
                cap.release()

    def close(self):
        """<summary>반복을 중단하고 스레드 종료를 기다린다.</summary>
        <input>호출 인수 또는 서비스 상태</input><output>처리 결과 또는 상태 갱신</output>
        <reason>종료 시 카메라 자원을 반환하기 위해서다.</reason>"""
        self.stop_event.set()
        with self.condition:
            self.condition.notify_all()
        if self.thread:
            self.thread.join(timeout=5)

    def stream(self):
        """<summary>최신 JPEG를 multipart 응답으로 반환한다.</summary>
        <input>호출 인수 또는 서비스 상태</input><output>처리 결과 또는 상태 갱신</output>
        <reason>여러 브라우저도 같은 생산자 결과를 사용한다.</reason>"""
        last = -1
        while not self.stop_event.is_set():
            with self.condition:
                self.condition.wait_for(lambda: self.sequence != last or self.error or self.stop_event.is_set(), timeout=3)
                if self.error or self.stop_event.is_set():
                    return
                if self.latest is None or self.sequence == last:
                    continue
                last, frame = self.sequence, self.latest
            yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + frame + b"\r\n"


def create_app(service):
    """<summary>로컬 실습용 Flask 앱과 경로를 만든다.</summary><param name="service">service 인수</param>
    <input>호출 인수 또는 서비스 상태</input><output>처리 결과 또는 상태 갱신</output>
    <reason>입력 서비스와 HTTP 처리를 분리해 검증한다.</reason>"""
    app = Flask(__name__)

    @app.get("/")
    def index():
        """<summary>영상·설정·로그 화면을 제공한다.</summary>
        <input>호출 인수 또는 서비스 상태</input><output>처리 결과 또는 상태 갱신</output>
        <reason>브라우저에서 흐름을 한눈에 확인한다.</reason>"""
        return render_template("index.html", modes=MODES)

    @app.get("/video_feed")
    @app.get("/detect_feed")
    @app.get("/stream")
    def stream():
        """<summary>최신 JPEG를 multipart 응답으로 반환한다.</summary>
        <input>호출 인수 또는 서비스 상태</input><output>처리 결과 또는 상태 갱신</output>
        <reason>여러 브라우저도 같은 생산자 결과를 사용한다.</reason>"""
        return Response(service.stream(), mimetype="multipart/x-mixed-replace; boundary=frame")

    @app.get("/api/status")
    def status():
        """<summary>현재 프레임 정보와 최근 로그를 반환한다.</summary>
        <input>호출 인수 또는 서비스 상태</input><output>처리 결과 또는 상태 갱신</output>
        <reason>카메라 실패도 정상 상태로 위장하지 않고 보여준다.</reason>"""
        with service.condition:
            with stages.LOCK:
                active = stages.ACTIVE
            return jsonify(**service.status, active=active, error=service.error, logs=list(service.logs)[-12:])

    @app.get("/api/pipeline")
    def pipeline_metadata():
        """<summary>단계별 XML 설명을 반환한다.</summary>
        <input>호출 인수 또는 서비스 상태</input><output>처리 결과 또는 상태 갱신</output>
        <reason>대시보드 노드가 코드 설명을 직접 사용한다.</reason>"""
        return jsonify(stages.metadata())

    @app.get("/events")
    def events():
        # SSE는 서버에서 브라우저로만 보내므로 별도 소켓 라이브러리가 필요 없다.
        """<summary>집계 상태를 SSE로 전송한다.</summary>
        <input>호출 인수 또는 서비스 상태</input><output>처리 결과 또는 상태 갱신</output>
        <reason>단방향 전송에 별도 소켓 라이브러리가 필요하지 않다.</reason>"""
        def generate():
            """<summary>200ms 간격으로 상태 스냅샷을 보낸다.</summary>
            <input>호출 인수 또는 서비스 상태</input><output>처리 결과 또는 상태 갱신</output>
            <reason>프레임마다 브라우저를 갱신하는 부하를 줄인다.</reason>"""
            while not service.stop_event.is_set():
                with service.condition:
                    with stages.LOCK:
                        active = stages.ACTIVE
                    data = {**service.status, "active": active, "error": service.error,
                            "logs": list(service.logs)[-12:]}
                yield "data: " + json.dumps(data, ensure_ascii=False) + "\n\n"
                service.stop_event.wait(.2)
        return Response(generate(), mimetype="text/event-stream", headers={"Cache-Control": "no-cache"})

    @app.post("/api/settings")
    def settings():
        """<summary>전처리·임계값·추론 간격을 검증하고 적용한다.</summary>
        <input>호출 인수 또는 서비스 상태</input><output>처리 결과 또는 상태 갱신</output>
        <reason>잘못된 입력으로 생산자 스레드가 종료되는 것을 막는다.</reason>"""
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return jsonify(error="JSON object required"), 400
        try:
            mode = data.get("mode", "original")
            confidence = float(data.get("confidence", .5))
            every = int(data.get("infer_every", 3))
            if mode not in MODES or not 0 <= confidence <= 1 or not 1 <= every <= 30:
                raise ValueError()
        except (TypeError, ValueError, OverflowError):
            return jsonify(error="Invalid mode, confidence, or inference interval"), 400
        with service.condition:
            service.mode, service.confidence, service.infer_every = mode, confidence, every
            service.log({"event": "settings", "mode": mode, "confidence": confidence, "infer_every": every})
        return jsonify(ok=True)

    @app.post("/capture")
    @app.post("/api/capture")
    def capture():
        """<summary>최신 프레임과 처리 정보를 파일로 저장한다.</summary>
        <input>호출 인수 또는 서비스 상태</input><output>처리 결과 또는 상태 갱신</output>
        <reason>다음 이미지 실습의 입력과 재현 근거를 함께 남긴다.</reason>"""
        with service.condition:
            if service.latest is None or service.error:
                return jsonify(error=service.error or "No frame yet"), 503
            frame, metadata = service.latest, dict(service.status)
        name = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S") + "-" + uuid.uuid4().hex[:8]
        (service.runtime / "captures" / f"{name}.jpg").write_bytes(frame)
        (service.runtime / "captures" / f"{name}.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
        with service.condition:
            service.log({"event": "capture", "name": name})
        return jsonify(url=f"/captures/{name}.jpg", metadata=metadata)

    @app.get("/api/captures")
    def captures():
        """<summary>최근 촬영 이미지 목록을 반환한다.</summary>
        <input>호출 인수 또는 서비스 상태</input><output>처리 결과 또는 상태 갱신</output>
        <reason>페이지 새로고침 없이 촬영 이력을 갱신한다.</reason>"""
        return jsonify([f"/captures/{p.name}" for p in sorted((service.runtime / "captures").glob("*.jpg"), reverse=True)[:12]])

    @app.get("/captures/<path:name>")
    def image(name):
        """<summary>저장 폴더 안의 촬영 파일만 제공한다.</summary><param name="name">name 인수</param>
        <input>호출 인수 또는 서비스 상태</input><output>처리 결과 또는 상태 갱신</output>
        <reason>send_from_directory로 상위 경로 접근을 막는다.</reason>"""
        return send_from_directory((service.runtime / "captures").resolve(), name)

    return app


def main(default_yolo=False):
    """<summary>공통 CLI 설정으로 서버를 실행하고 종료를 정리한다.</summary><param name="default_yolo">default_yolo 인수</param>
    <input>호출 인수 또는 서비스 상태</input><output>처리 결과 또는 상태 갱신</output>
    <reason>단계별 진입점이 같은 검증된 엔진을 공유한다.</reason>"""
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", choices=("synthetic", "camera"), default="synthetic")
    parser.add_argument("--camera", type=int, default=0)
    parser.add_argument("--yolo", action="store_true", default=default_yolo)
    parser.add_argument("--weights", default="yolo26n.pt")
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--size", type=int, default=320)
    parser.add_argument("--port", type=int, default=5050)
    parser.add_argument("--classes", nargs="*")
    parser.add_argument("--skip", type=int, default=3)
    args = parser.parse_args()
    detector = YoloDetector(args.weights, args.device, args.size, args.classes) if args.yolo else None
    service = CameraService(args.source, args.camera, detector)
    if not 1 <= args.skip <= 30:
        parser.error("--skip must be between 1 and 30")
    service.infer_every = args.skip
    service.start()
    try:
        create_app(service).run(host="127.0.0.1", port=args.port, threaded=True, use_reloader=False)
    finally:
        service.close()


if __name__ == "__main__":
    main()

