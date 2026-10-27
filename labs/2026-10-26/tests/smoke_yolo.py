"""실제 모델·표준 예제 이미지로 추론 경로를 확인한다. 카메라 시험은 아니다."""
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'vision'))
import cv2
from ultralytics.utils import ASSETS
from pipeline import PIPELINE
from step8_pipeline_dashboard import Detector,OutputStore,preprocess,run_inference,postprocess,visualize,output


def main():
    """<summary>실제 YOLO 결과와 시간·JPEG 출력을 검증한다.</summary><input>패키지 표준 bus 이미지와 모델</input><output>JSON 검증 기록</output><reason>모의 검출기 시험을 실제 모델 추론과 구분한다.</reason>"""
    image=cv2.imread(str(ASSETS/'bus.jpg'))
    if image is None:
        raise RuntimeError('Ultralytics bus sample missing')
    detector=Detector(device='cuda:0') # CPU 러너에서 명시적 폴백을 검사한다.
    PIPELINE.begin_frame()
    frame=preprocess(image)
    result=run_inference(detector,frame,{'skip':1,'imgsz':320,'conf':.25},1)
    detections=postprocess(result,[],set())
    if not detections:
        raise AssertionError('Expected detections on standard bus image')
    store=OutputStore()
    output(store,frame,visualize(frame,detections))
    PIPELINE.end_frame()
    if not store.detect.startswith(b'\xff\xd8'):
        raise AssertionError('Output JPEG missing')
    snapshot=PIPELINE.snapshot()
    if next(s for s in snapshot['stages'] if s['id']=='inference')['execution_avg_ms']<=0:
        raise AssertionError('Inference timing missing')
    report=dict(model=detector.path,device=detector.device,input='Ultralytics packaged bus.jpg; not camera',detections=[dict(label=d.label,confidence=round(d.confidence,4),xyxy=[round(x,1) for x in d.xyxy]) for d in detections],model_speed_ms=result.speed,stages=snapshot['stages'],jpeg_bytes=len(store.detect))
    Path('runtime').mkdir(exist_ok=True)
    Path('runtime/yolo_smoke.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
    print('REAL_YOLO_PASS '+json.dumps({k:report[k] for k in ('model','device','input','jpeg_bytes')},ensure_ascii=False))
    print('DETECTIONS '+json.dumps(report['detections'],ensure_ascii=False))
    store.close()


if __name__=='__main__':
    main()
