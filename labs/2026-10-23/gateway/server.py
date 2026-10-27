"""python server.py --url http://보드IP/stream. 기본 바인딩은 localhost다."""
import argparse
from pathlib import Path
import sys

VISION=Path(__file__).resolve().parents[2]/"2026-10-22"/"vision"
sys.path.insert(0,str(VISION))
from app import CameraService,create_app
from pipeline import YoloDetector
from remote import RemoteReader


def main():
    """<summary>원격 영상 입력으로 기존 비전 대시보드를 실행한다.</summary>
    <input>보드 URL·모델 설정</input><output>Flask 앱</output>
    <reason>한 게이트웨이가 보드 스트림을 받아 여러 브라우저에 전달한다.</reason>"""
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url",required=True)
    parser.add_argument("--no-yolo",action="store_true")
    parser.add_argument("--model",default="yolo26n.pt")
    parser.add_argument("--device",default="cpu")
    parser.add_argument("--size",type=int,default=320)
    parser.add_argument("--port",type=int,default=5050)
    args=parser.parse_args()
    detector=None if args.no_yolo else YoloDetector(args.model,args.device,args.size)
    reader=RemoteReader(args.url)
    service=CameraService(source="remote",reader=reader,detector=detector,runtime=Path(__file__).parent/"runtime")
    service.start()
    try:
        create_app(service).run(host="127.0.0.1",port=args.port,threaded=True,use_reloader=False)
    finally:
        service.close()
        reader.release()


if __name__=="__main__":
    main()
