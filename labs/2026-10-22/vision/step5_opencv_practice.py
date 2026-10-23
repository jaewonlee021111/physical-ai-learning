"""실행: python step5_opencv_practice.py. 1~6 모드, s 저장, q 종료.
확인: 원본·회색·블러·엣지·이진화·HSV, 이동평균 FPS.
"""
import argparse
from collections import deque
from pathlib import Path
from time import perf_counter, time_ns
import cv2
import numpy as np
from camera import frames
from pipeline import as_bgr, preprocess


def noop(value):
    """<summary>트랙바 변경 콜백이다.</summary><param name="value">현재 값</param>
    <input>정수</input><output>없음</output><reason>값은 프레임 루프에서 함께 읽는다.</reason>"""
    pass


def main():
    """<summary>전처리 모드를 키보드로 바꾸며 비교한다.</summary>
    <input>CLI·키보드·HSV 범위</input><output>창과 저장 이미지</output>
    <reason>이 그리기 함수는 이후 객체 박스 시각화에도 쓰인다.</reason>"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", choices=("camera", "synthetic"), default="camera")
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--frames", type=int, default=0)
    args = parser.parse_args()
    modes = ["original", "gray", "blur", "edges", "threshold", "hsv"]
    mode = "original"
    if not args.headless:
        cv2.namedWindow("STEP 5")
        for name, value, maximum in [("H min", 15, 179), ("H max", 45, 179), ("S min", 80, 255), ("S max", 255, 255), ("V min", 60, 255), ("V max", 255, 255)]:
            cv2.createTrackbar(name, "STEP 5", value, maximum, noop)
    source = frames(args.source)
    times = deque(maxlen=30)
    previous = perf_counter()
    try:
        for count, frame in enumerate(source, 1):
            if args.headless:
                mode = modes[(count-1) % len(modes)]
            output = as_bgr(preprocess(frame, mode), mode)
            if mode == "hsv" and not args.headless:
                lower = np.array([cv2.getTrackbarPos(f"{c} min", "STEP 5") for c in "HSV"])
                upper = np.array([cv2.getTrackbarPos(f"{c} max", "STEP 5") for c in "HSV"])
                mask = cv2.inRange(cv2.cvtColor(frame, cv2.COLOR_BGR2HSV), lower, upper)
                output = cv2.bitwise_and(frame, frame, mask=mask)
            now = perf_counter()
            times.append(now-previous)
            previous = now
            fps = len(times) / max(sum(times), 1e-9)
            cv2.rectangle(output, (5, 5), (350, 35), (35,35,35), -1)
            cv2.putText(output, f"{mode} / FPS {fps:.1f}", (12, 27), cv2.FONT_HERSHEY_SIMPLEX, .6, (230,230,230), 1)
            if not args.headless:
                cv2.imshow("STEP 5", output)
                key = cv2.waitKey(1) & 255
                if ord("1") <= key <= ord("6"):
                    mode = modes[key - ord("1")]
                elif key == ord("s"):
                    Path("runtime").mkdir(exist_ok=True)
                    cv2.imwrite(f"runtime/step5-{time_ns()}.jpg", output)
                elif key == ord("q"):
                    break
            if args.frames and count >= args.frames:
                break
        print({"frames": count, "last_mode": mode, "source": args.source})
    finally:
        source.close()
        if not args.headless:
            cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
