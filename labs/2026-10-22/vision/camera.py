"""실제 장치를 임의로 대체하지 않는 카메라 입력 도구."""
import cv2
import config
from pipeline import synthetic_frame


def probe_cameras(backend=None):
    """<summary>0~3번 카메라를 열어 접근 가능 여부를 검사한다.</summary>
    <param name="backend">OpenCV 백엔드 또는 없음</param><input>장치 번호 0~3</input>
    <output>접근 가능한 번호 목록</output><reason>카메라 번호가 항상 0은 아니다.</reason>"""
    found = []
    for index in range(4):
        cap = cv2.VideoCapture(index) if backend is None else cv2.VideoCapture(index, backend)
        try:
            if cap.isOpened() and cap.read()[0]:
                found.append(index)
        finally:
            cap.release()
    return found


def frames(source="camera", index=config.CAMERA_INDEX, backend=None):
    """<summary>프레임을 순서대로 반환하고 종료 시 장치를 해제한다.</summary>
    <param name="source">camera 또는 synthetic</param><param name="index">장치 번호</param>
    <param name="backend">Windows DSHOW 등의 선택 백엔드</param><input>카메라 설정</input>
    <output>BGR uint8 프레임</output><reason>장비 오류를 합성 영상으로 숨기지 않는다.</reason>"""
    cap = None
    try:
        if source == "camera":
            cap = cv2.VideoCapture(index) if backend is None else cv2.VideoCapture(index, backend)
            if not cap.isOpened():
                raise RuntimeError(f"카메라 {index}를 열 수 없습니다. USB·OS 권한·Zoom 점유를 확인하세요.")
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.FRAME_WIDTH)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.FRAME_HEIGHT)
            print({"actual_width": cap.get(cv2.CAP_PROP_FRAME_WIDTH),
                   "actual_height": cap.get(cv2.CAP_PROP_FRAME_HEIGHT), "camera_fps": cap.get(cv2.CAP_PROP_FPS)})
        tick = 0
        while True:
            if cap is None:
                image = synthetic_frame(tick * 4)
            else:
                ok, image = cap.read()
                if not ok or image is None:
                    raise RuntimeError("카메라 프레임을 읽을 수 없습니다.")
            yield image
            tick += 1
    finally:
        if cap is not None:
            cap.release()
