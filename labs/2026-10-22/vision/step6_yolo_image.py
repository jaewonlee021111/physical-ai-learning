"""실행: python step6_yolo_image.py --image 사진.jpg.
확인: 320·416·640 워밍업 제외 시간, 탐지 표, 수동 박스와 plot() 비교.
"""
import argparse
import hashlib
import json
from pathlib import Path
from time import perf_counter
import cv2
import config
from pipeline import YoloDetector, draw_objects


def benchmark(image_path, out, weights=config.MODEL_PATH, device=config.DEVICE):
    """<summary>같은 사진의 입력 크기별 추론을 측정한다.</summary>
    <param name="image_path">입력 파일</param><param name="out">출력 폴더</param>
    <param name="weights">모델 가중치</param><param name="device">추론 장치</param>
    <input>실제 사진</input><output>JSON 측정값과 비교 JPEG</output>
    <reason>첫 로딩을 제외하고 해상도별 비용을 공정하게 비교한다.</reason>"""
    image = cv2.imread(str(image_path))
    if image is None:
        raise ValueError("사진 파일을 읽을 수 없습니다.")
    detector = YoloDetector(weights, device)
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    rows = []
    for size in (320, 416, 640):
        detector.size = size
        detector.detect(image, .4)
        start = perf_counter()
        objects = detector.detect(image, .4)
        elapsed = (perf_counter()-start)*1000
        result = detector.last_result
        manual = draw_objects(image.copy(), objects)
        cv2.imwrite(str(out/f"yolo-{size}.jpg"), cv2.hconcat([manual, result.plot()]))
        row = {"imgsz": size, "wall_ms": round(elapsed, 3), "speed_ms": result.speed,
               "count": len(objects), "detections": objects}
        rows.append(row)
        print(f"imgsz={size} / {elapsed:.2f} ms / {len(objects)} objects")
        for obj in objects:
            print(f"  {obj['label']:16} {obj['confidence']:.3f}  {obj['xyxy']}")
    report = {"model": weights, "device": device, "warmup_excluded": True,
              "input_sha256": hashlib.sha256(Path(image_path).read_bytes()).hexdigest(), "runs": rows}
    (out/"yolo-benchmark.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=Path("runtime/yolo"))
    parser.add_argument("--model", default=config.MODEL_PATH)
    parser.add_argument("--device", default=config.DEVICE)
    args = parser.parse_args()
    try:
        benchmark(args.image, args.out, args.model, args.device)
    except Exception as exc:
        parser.exit(1, f"추론 실패: {exc}\n모델 호환 문제라면 --model yolo11n.pt로 비교하세요.\n")
