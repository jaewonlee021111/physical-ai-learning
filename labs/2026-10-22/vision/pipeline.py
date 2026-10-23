"""OpenCV input → preprocessing → optional YOLO → annotation → JPEG.

Synthetic input is explicitly a demo, never a substitute for real YOLO inference.
"""
from pathlib import Path
from time import perf_counter
import cv2
import numpy as np
from stages import stage

MODES = ("original", "rgb", "gray", "blur", "edges", "threshold", "hsv")


@stage("capture")
def synthetic_frame(tick=0):
    """<summary>카메라 없이 움직이는 도형 프레임을 생성한다.</summary>
    <param name="tick">도형 위치를 바꾸는 순번</param><input>정수 순번</input>
    <output>BGR uint8 배열</output><reason>장비 없이 서버를 검증하기 위한 명시적 합성 입력이다.</reason>"""
    frame = np.zeros((360, 640, 3), dtype=np.uint8)
    frame[:] = (38, 28, 22)
    cv2.rectangle(frame, (50 + tick % 250, 80), (180 + tick % 250, 220), (60, 190, 240), -1)
    cv2.circle(frame, (470, 180), 65, (220, 110, 60), -1)
    cv2.putText(frame, "SYNTHETIC INPUT / NO CAMERA", (25, 325), cv2.FONT_HERSHEY_SIMPLEX, .65, (245, 245, 245), 1)
    return frame


@stage("preprocess")
def preprocess(frame, mode):
    """<summary>이미지의 색 공간과 특징을 변환한다.</summary>
    <param name="frame">BGR 원본</param><param name="mode">변환 모드</param>
    <input>H×W×3 uint8</input><output>컬러 또는 단일 채널 배열</output>
    <reason>모델에 입력하기 전 비용과 정보 손실을 관찰한다.</reason>"""
    if mode not in MODES:
        raise ValueError(f"mode must be one of {MODES}")
    if mode == "rgb":
        # This array is RGB. Convert it back before passing it to a BGR encoder/model.
        return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    if mode == "gray":
        return cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    if mode == "edges":
        return cv2.Canny(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), 80, 160)
    if mode == "blur":
        return cv2.GaussianBlur(frame, (9, 9), 0)
    if mode == "threshold":
        return cv2.threshold(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), 127, 255, cv2.THRESH_BINARY)[1]
    if mode == "hsv":
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, np.array([15, 80, 60]), np.array([45, 255, 255]))
        return cv2.bitwise_and(frame, frame, mask=mask)
    return frame.copy()


def as_bgr(image, mode):
    """<summary>인코더·모델이 받을 BGR 배열로 맞춘다.</summary>
    <param name="image">변환된 배열</param><param name="mode">원래 변환 모드</param>
    <input>RGB·BGR·회색 배열</input><output>BGR 배열</output>
    <reason>RGB를 그대로 imencode하면 빨강과 파랑이 뒤바뀐다.</reason>"""
    if image.ndim == 2:
        return cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    return cv2.cvtColor(image, cv2.COLOR_RGB2BGR) if mode == "rgb" else image.copy()


class YoloDetector:
    """<summary>한 번 로드한 YOLO 모델을 반복 사용한다.</summary>
    <input>가중치와 추론 설정</input><output>탐지 어댑터</output>
    <reason>매 프레임 모델을 다시 읽는 비용을 막는다.</reason>"""
    def __init__(self, weights="yolo26n.pt", device="cpu", size=320, classes=None):
        """<summary>모델을 로드한다.</summary><param name="weights">가중치 경로</param>
        <param name="device">cpu·cuda:0·mps</param><param name="size">입력 크기</param>
        <param name="classes">표시할 클래스명</param><input>설정</input><output>모델 인스턴스</output>
        <reason>장치별 비교가 가능하도록 설정을 분리한다.</reason>"""
        from ultralytics import YOLO
        self.model = YOLO(weights)
        self.device, self.size = device, size
        self.classes = classes
        self.last_result = None

    @stage("inference")
    def detect(self, frame, confidence):
        """<summary>객체의 박스·클래스·점수를 구한다.</summary>
        <param name="frame">BGR 배열</param><param name="confidence">점수 임계값</param>
        <input>프레임</input><output>박스 목록</output>
        <reason>모델 내부 세 단계 시간은 Results.speed로 별도 구분한다.</reason>"""
        options = {"half": True} if self.device.startswith("cuda") else {}
        result = self.model.predict(frame, device=self.device, imgsz=self.size,
                                    conf=confidence, verbose=False, **options)[0]
        self.last_result = result
        return select_objects(result, self.classes)


@stage("postprocess")
def select_objects(result, classes=None):
    """<summary>모델 결과를 표시용 박스 목록으로 바꾼다.</summary>
    <param name="result">Ultralytics Results</param><param name="classes">클래스 필터</param>
    <input>탐지 텐서</input><output>JSON 가능한 목록</output>
    <reason>텐서를 웹 응답으로 직접 보낼 수 없기 때문이다.</reason>"""
    return [{"label": result.names[int(box.cls.item())],
             "confidence": round(float(box.conf.item()), 4),
             "xyxy": [round(float(v), 2) for v in box.xyxy[0].tolist()]}
            for box in result.boxes
            if not classes or result.names[int(box.cls.item())] in classes]


@stage("visualize")
def draw_objects(canvas, objects):
    """<summary>객체 위치와 점수를 프레임에 그린다.</summary>
    <param name="canvas">BGR 프레임</param><param name="objects">탐지 목록</param>
    <input>프레임·박스</input><output>주석이 그려진 배열</output>
    <reason>rectangle과 putText를 5~7단계에서 재사용한다.</reason>"""
    for obj in objects:
        x1, y1, x2, y2 = map(int, obj["xyxy"])
        cv2.rectangle(canvas, (x1, y1), (x2, y2), (70, 230, 160), 2)
        cv2.putText(canvas, f'{obj["label"]} {obj["confidence"]:.2f}',
                    (x1, max(18, y1 - 8)), cv2.FONT_HERSHEY_SIMPLEX, .5, (70, 230, 160), 1)
    return canvas


@stage("output")
def encode(canvas):
    """<summary>웹에서 볼 수 있는 JPEG 바이트로 압축한다.</summary>
    <param name="canvas">BGR 배열</param><input>시각화 프레임</input><output>JPEG 바이트</output>
    <reason>MJPEG 스트림은 연속된 JPEG 이미지로 구성된다.</reason>"""
    ok, encoded = cv2.imencode(".jpg", canvas)
    if not ok:
        raise RuntimeError("JPEG encoding failed")
    return encoded.tobytes()


def process(frame, mode="original", detector=None, confidence=.5, cached_objects=None):
    """<summary>한 프레임을 변환·추론·시각화·압축한다.</summary>
    <param name="frame">BGR 입력</param><param name="mode">전처리 모드</param>
    <param name="detector">YOLO 또는 없음</param><param name="confidence">임계값</param>
    <param name="cached_objects">추론 생략 시 이전 박스</param>
    <input>프레임과 설정</input><output>JPEG와 계측 정보</output>
    <reason>웹과 이미지·창 실습에서 동일한 처리 코드를 사용한다.</reason>"""
    timings = {}
    start = perf_counter()
    processed = preprocess(frame, mode)
    canvas = as_bgr(processed, mode)
    timings["preprocess"] = (perf_counter() - start) * 1000
    start = perf_counter()
    objects = detector.detect(canvas, confidence) if detector else (cached_objects or [])
    call_ms = (perf_counter() - start) * 1000
    speed = getattr(getattr(detector, "last_result", None), "speed", {}) or {}
    timings["model_preprocess"] = speed.get("preprocess", 0)
    timings["inference"] = speed.get("inference", call_ms) if detector else 0
    timings["postprocess"] = speed.get("postprocess", 0)
    start = perf_counter()
    canvas = draw_objects(canvas, objects)
    timings["visualize"] = (perf_counter() - start) * 1000
    start = perf_counter()
    encoded = encode(canvas)
    timings["output"] = (perf_counter() - start) * 1000
    return encoded, {"mode": mode, "shape": list(processed.shape),
                               "detections": objects, "inference_enabled": detector is not None,
                               "model_call_ms": round(call_ms, 3),
                               "timings_ms": {k: round(float(v), 3) for k, v in timings.items()}}


def save_comparison(frame, directory):
    """<summary>전처리별 실제 이미지를 저장한다.</summary>
    <param name="frame">입력 배열</param><param name="directory">출력 폴더</param>
    <input>이미지</input><output>모드별 JPEG 파일</output>
    <reason>실행 결과를 눈으로 비교할 수 있게 남긴다.</reason>"""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    for mode in MODES:
        data, _ = process(frame, mode)
        (directory / f"{mode}.jpg").write_bytes(data)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", type=Path)
    parser.add_argument("--out", type=Path, default=Path("runtime/comparison"))
    args = parser.parse_args()
    image = cv2.imread(str(args.image)) if args.image else synthetic_frame()
    if image is None:
        parser.error("이미지 파일을 읽을 수 없습니다")
    save_comparison(image, args.out)
    print(f"Saved {len(MODES)} preprocessing images to {args.out}")
