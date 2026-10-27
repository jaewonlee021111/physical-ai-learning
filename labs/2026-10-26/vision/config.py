"""환경변수를 우선하는 실습 설정. 실제 주소와 계정 정보는 커밋하지 않는다."""
import os
CAMERA_URL=os.getenv("CAMERA_URL","http://192.168.0.50/stream")
SOURCE=os.getenv("SOURCE","esp32")
WEBCAM_INDEX=int(os.getenv("WEBCAM_INDEX","0"))
MODEL_PATH=os.getenv("MODEL_PATH","yolo26n.pt")
FALLBACK_MODEL_PATH=os.getenv("FALLBACK_MODEL_PATH","yolo11n.pt")
DEVICE=os.getenv("DEVICE","cpu")
IMG_SIZE=int(os.getenv("IMG_SIZE","320"))
CONF=float(os.getenv("CONF","0.4"))
SKIP=int(os.getenv("SKIP","2"))
HOST=os.getenv("HOST","127.0.0.1")
PORT=int(os.getenv("PORT","5000"))
SSE_INTERVAL_SEC=0.2
LOG_MAXLEN=500
STAT_WINDOW=30
SSE_MAX_LOGS=60
LOG_EVERY=5
STREAM_TIMEOUT_SEC=2.0
RECONNECT_DELAY_SEC=1.0
JPEG_QUALITY=80
CAPTURE_DIR=os.getenv("CAPTURE_DIR","runtime/captures")
