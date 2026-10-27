"""사용자 PC에서만 가능한 카메라·보드 확인. 결과는 runtime/pc-check.json에만 저장한다."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys
from time import perf_counter, sleep
import cv2

HERE = Path(__file__).resolve().parent


def camera_check(index, frame_count=30, yolo=False):
    """<summary>실제 카메라 프레임을 읽고 선택적으로 YOLO를 실행한다.</summary>
    <param name="index">사용자가 선택한 카메라 번호</param>
    <param name="frame_count">읽을 프레임 수</param><param name="yolo">실제 추론 여부</param>
    <input>USB 또는 내장 카메라</input><output>성공·배열 정보·시간·탐지 목록</output>
    <reason>합성 입력 검사와 실제 하드웨어 검사를 구분한다.</reason>"""
    cap = cv2.VideoCapture(index)
    try:
        if not cap.isOpened():
            return {"status":"unavailable", "index":index}
        start = perf_counter()
        image = None
        for _ in range(frame_count):
            ok, image = cap.read()
            if not ok or image is None:
                return {"status":"read_failed", "index":index}
        elapsed = perf_counter()-start
        report = {"status":"passed", "index":index, "frames_read":frame_count,
                  "shape":list(image.shape), "dtype":str(image.dtype),
                  "elapsed_seconds":round(elapsed,3), "source":"physical_camera"}
        if yolo:
            from pipeline import YoloDetector, process
            _, result = process(image, detector=YoloDetector())
            report["yolo"] = result
        # 얼굴 사진은 저장하지 않고 숫자와 결과만 남긴다.
        return report
    finally:
        cap.release()


def board_check(board, port=None):
    """<summary>보드를 빌드하고 명시한 포트에만 업로드·시리얼 확인한다.</summary>
    <param name="board">uno 또는 esp32s3</param><param name="port">사용자가 지정한 장치 포트</param>
    <input>실제 보드 프로젝트</input><output>빌드·업로드·heartbeat 상태</output>
    <reason>연결된 다른 장치를 추측으로 덮어쓰지 않는다.</reason>"""
    project = HERE.parent/"firmware"/board
    command = [sys.executable,"-m","platformio","run","-d",str(project)]
    built = subprocess.run(command, capture_output=True, text=True)
    report = {"board":board,"build_exit_code":built.returncode,"uploaded":False}
    if built.returncode:
        report["error"] = "컴파일 실패. 터미널의 PlatformIO 오류를 확인하세요."
        print(built.stdout)
        print(built.stderr, file=sys.stderr)
        return report
    if port is None:
        report["status"] = "built_only_no_port_selected"
        return report
    uploaded = subprocess.run(command+["-t","upload","--upload-port",port],capture_output=True,text=True)
    report.update(upload_exit_code=uploaded.returncode,uploaded=uploaded.returncode==0,port=port)
    if uploaded.returncode:
        print(uploaded.stdout)
        print(uploaded.stderr,file=sys.stderr)
        return report
    import serial
    sleep(2)
    try:
        with serial.Serial(port,115200,timeout=1) as connection:
            deadline = perf_counter()+10
            lines = []
            while perf_counter()<deadline:
                line = connection.readline().decode(errors="replace").strip()
                if line:
                    lines.append(line)
                if "heartbeat" in line:
                    break
        report["heartbeat_received"] = any("heartbeat" in line for line in lines)
        report["serial_lines"] = lines[-10:]
    except serial.SerialException as exc:
        report["serial_error"] = str(exc)
    return report


def main():
    """<summary>로컬 장비 검사 결과를 파일로 남긴다.</summary>
    <input>CLI에서 명시한 카메라·보드·포트</input><output>runtime/pc-check.json</output>
    <reason>원격 에이전트가 확인하지 않은 장비 상태를 완료로 표시하지 않는다.</reason>"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--camera",type=int)
    parser.add_argument("--yolo",action="store_true")
    parser.add_argument("--board",choices=("uno","esp32s3"))
    parser.add_argument("--port",help="실제 장치를 확인한 뒤 명시. 없으면 업로드하지 않음")
    args = parser.parse_args()
    if args.port and not args.board:
        parser.error("--port는 --board와 함께 지정해야 합니다.")
    report = {"checked_at":datetime.now(timezone.utc).isoformat(),"camera":"not_requested","board":"not_requested"}
    if args.camera is not None:
        report["camera"] = camera_check(args.camera,yolo=args.yolo)
    if args.board:
        report["board"] = board_check(args.board,args.port)
    if args.camera is None and args.board is None:
        print("카메라: python pc_check.py --camera 0 --yolo")
        print("보드 목록: python -m platformio device list")
        print("빌드만: python pc_check.py --board uno")
        print("선택한 보드 업로드: python pc_check.py --board uno --port COM4")
    destination = HERE/"runtime"/"pc-check.json"
    destination.parent.mkdir(exist_ok=True)
    destination.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(report,ensure_ascii=False,indent=2))
    print("저장:",destination)
    camera_failed = isinstance(report["camera"],dict) and report["camera"]["status"] != "passed"
    board = report["board"]
    board_failed = isinstance(board,dict) and (board.get("build_exit_code") != 0 or
                   (args.port is not None and not board.get("heartbeat_received",False)))
    if camera_failed or board_failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
