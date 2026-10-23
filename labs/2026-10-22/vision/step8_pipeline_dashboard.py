"""실행: python step8_pipeline_dashboard.py --source camera --device cpu.
확인: /api/pipeline의 XML 설명, /events SSE, 병목·로그·샘플링 표시.
카메라 없는 서버 검사: --source synthetic --no-yolo.
"""
from step7_realtime_yolo import main

if __name__ == "__main__":
    main(default_mode="web")
