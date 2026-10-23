"""실행: python step1_webcam.py --probe / --source camera. q 종료.
확인: 실제 해상도·FPS, shape·dtype, 픽셀은 BGR 순서다.
"""
import argparse
from collections import deque
from time import perf_counter
import cv2
from camera import frames, probe_cameras


def main():
    """<summary>카메라 미리보기 또는 명시적 합성 검사를 실행한다.</summary>
    <input>CLI 옵션</input><output>창 또는 프레임 정보</output>
    <reason>입력 단계가 동작하는지 모델 없이 먼저 확인한다.</reason>"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", choices=("camera", "synthetic"), default="camera")
    parser.add_argument("--camera", type=int, default=0)
    parser.add_argument("--probe", action="store_true")
    parser.add_argument("--dshow", action="store_true")
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--frames", type=int, default=0)
    args = parser.parse_args()
    backend = cv2.CAP_DSHOW if args.dshow else None
    if args.probe:
        print("사용 가능:", probe_cameras(backend))
        return
    source = frames(args.source, args.camera, backend)
    times = deque(maxlen=30)
    previous = perf_counter()
    try:
        for count, frame in enumerate(source, 1):
            now = perf_counter()
            times.append(now - previous)
            previous = now
            fps = len(times) / max(sum(times), 1e-9)
            if count == 1:
                print({"source": args.source, "shape": frame.shape, "dtype": str(frame.dtype), "BGR[y=100,x=100]": frame[100, 100].tolist()})
            if not args.headless:
                cv2.putText(frame, f"FPS {fps:.1f}", (15, 25), cv2.FONT_HERSHEY_SIMPLEX, .6, (220, 220, 220), 1)
                cv2.imshow("STEP 1", frame)
                if cv2.waitKey(1) & 255 == ord("q"):
                    break
            if args.frames and count >= args.frames:
                break
    finally:
        source.close()
        if not args.headless:
            cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
