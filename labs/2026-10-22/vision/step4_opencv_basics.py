"""실행: python step4_opencv_basics.py --image runtime/captures/이름.jpg.
--synthetic이면 카메라 없이 검사. 결과는 runtime/comparison/에 저장한다.
"""
import argparse
import json
from pathlib import Path
import cv2
from camera import frames
from pipeline import as_bgr, preprocess, save_comparison, synthetic_frame


def main():
    """<summary>이미지 배열 정보와 색 순서·좌표를 비교한다.</summary>
    <input>파일 또는 카메라·합성 입력</input><output>비교 JPEG와 배열 정보</output>
    <reason>픽셀 좌표와 배열 인덱스의 차이를 실제 값으로 보여준다.</reason>"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", type=Path)
    parser.add_argument("--synthetic", action="store_true")
    parser.add_argument("--out", type=Path, default=Path("runtime/comparison"))
    args = parser.parse_args()
    image = cv2.imread(str(args.image)) if args.image else None
    if image is None:
        if args.synthetic:
            image = synthetic_frame()
        else:
            source = frames()
            try:
                image = next(source)
            finally:
                source.close()
    rgb = preprocess(image, "rgb")
    x, y = min(100, image.shape[1]-1), min(50, image.shape[0]-1)
    info = {"shape": list(image.shape), "dtype": str(image.dtype),
            "min": int(image.min()), "max": int(image.max()), "coordinate_xy": [x, y],
            "array_yx": [y, x], "BGR_pixel": image[y, x].tolist(), "RGB_pixel": rgb[y, x].tolist()}
    print(json.dumps(info, ensure_ascii=False, indent=2))
    save_comparison(image, args.out)
    panels = []
    for label, panel in [("BGR / correct", image.copy()),
                         ("RGB as BGR / wrong colors", rgb.copy()),
                         ("GRAY", as_bgr(preprocess(image, "gray"), "gray"))]:
        cv2.putText(panel, label, (12, 25), cv2.FONT_HERSHEY_SIMPLEX, .55, (255,255,255), 1)
        panels.append(panel)
    cv2.imwrite(str(args.out / "comparison.jpg"), cv2.hconcat(panels))
    (args.out / "info.json").write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()

