"""실행: python step7_realtime_yolo.py --mode web --source camera.
확인: CPU/GPU·입력 크기·skip·클래스 필터에 따른 속도와 오인식.
"""
import argparse
from collections import deque
from pathlib import Path
from time import perf_counter
import cv2
import numpy as np
import config
from app import CameraService, create_app
from camera import frames
from pipeline import YoloDetector, process


def main(default_mode="window"):
    """<summary>실시간 탐지를 창 또는 웹에서 실행한다.</summary>
    <param name="default_mode">기본 출력 방식</param><input>카메라·추론 옵션</input>
    <output>탐지 영상·로그</output><reason>같은 모델로 창과 웹 출력을 비교한다.</reason>"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("window", "web"), default=default_mode)
    parser.add_argument("--source", choices=("camera", "synthetic"), default="camera")
    parser.add_argument("--camera", type=int, default=config.CAMERA_INDEX)
    parser.add_argument("--device", default=config.DEVICE)
    parser.add_argument("--imgsz", type=int)
    parser.add_argument("--conf", type=float, default=.4)
    parser.add_argument("--skip", type=int)
    parser.add_argument("--model", default=config.MODEL_PATH)
    parser.add_argument("--classes", nargs="*")
    parser.add_argument("--openvino", action="store_true")
    parser.add_argument("--no-yolo", action="store_true", help="입력·서버만 검사하며 탐지는 하지 않음")
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--frames", type=int, default=0)
    parser.add_argument("--port", type=int, default=5050)
    args = parser.parse_args()
    size = args.imgsz if args.imgsz is not None else (640 if args.device.startswith("cuda") else 320)
    skip = args.skip if args.skip is not None else (1 if args.device.startswith("cuda") else 2)
    if not 1 <= skip <= 30 or not 0 <= args.conf <= 1 or size < 32:
        parser.error("skip은 1~30, conf는 0~1, imgsz는 32 이상이어야 합니다.")
    weights = args.model
    if args.openvino:
        weights = str(Path(args.model).with_suffix("")) + "_openvino_model"
        if not Path(weights).is_dir():
            parser.error("OpenVINO 모델 폴더가 없습니다. 먼저 yolo export를 실행하세요.")
    detector = None if args.no_yolo else YoloDetector(weights, args.device, size, args.classes)
    if args.mode == "web":
        service = CameraService(args.source, args.camera, detector)
        service.confidence, service.infer_every = args.conf, skip
        service.start()
        try:
            create_app(service).run(host="127.0.0.1", port=args.port, threaded=True, use_reloader=False)
        finally:
            service.close()
        return
    source = frames(args.source, args.camera)
    cached = []
    durations = deque(maxlen=30)
    previous = perf_counter()
    try:
        for number, frame in enumerate(source):
            active = detector if number % skip == 0 else None
            jpeg, info = process(frame, detector=active, confidence=args.conf, cached_objects=cached)
            if active:
                cached = info["detections"]
            now = perf_counter()
            durations.append(now-previous)
            previous = now
            if not args.headless:
                image = cv2.imdecode(np.frombuffer(jpeg, np.uint8), cv2.IMREAD_COLOR)
                text = f"{args.device} / {len(durations)/max(sum(durations),1e-9):.1f} FPS / {info['timings_ms']['inference']:.1f} ms / {len(cached)} boxes"
                cv2.putText(image, text, (12, 28), cv2.FONT_HERSHEY_SIMPLEX, .5, (220,220,220), 1)
                cv2.imshow("STEP 7", image)
                if cv2.waitKey(1) & 255 == ord("q"):
                    break
            if args.frames and number + 1 >= args.frames:
                break
        print({"source": args.source, "device": args.device, "frames": number+1,
               "imgsz": size, "skip": skip, "yolo_enabled": detector is not None})
    finally:
        source.close()
        if not args.headless:
            cv2.destroyAllWindows()


if __name__ == "__main__":
    main()

