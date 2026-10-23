"""python verify.py: 합성 입력·실제 HTTP·단위 테스트를 재현하고 근거를 저장한다."""
import io
import json
from pathlib import Path
import platform
import tempfile
import threading
import unittest
import urllib.request
import cv2
import numpy as np
from werkzeug.serving import make_server
from app import CameraService, create_app
import test_vision


def main():
    """<summary>단위 검사와 실제 로컬 HTTP 요청을 실행한다.</summary>
    <input>합성 프레임</input><output>실행 기록 JSON·텍스트</output>
    <reason>테스트 클라이언트와 실제 서버 응답을 함께 확인한다.</reason>"""
    evidence = Path(__file__).resolve().parent.parent / "evidence"
    evidence.mkdir(exist_ok=True)
    output = io.StringIO()
    result = unittest.TextTestRunner(stream=output, verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(test_vision))
    (evidence/"unit-tests.txt").write_text(output.getvalue(), encoding="utf-8")
    report = {"python":platform.python_version(), "opencv":cv2.__version__, "numpy":np.__version__,
              "unit_tests":{"run":result.testsRun,"failures":len(result.failures),"errors":len(result.errors)},
              "camera_hardware_tested":False,"gpu_tested":False,"browser_ui_tested":False}
    with tempfile.TemporaryDirectory() as directory:
        service = CameraService(runtime=Path(directory))
        server = make_server("127.0.0.1", 0, create_app(service), threaded=True)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        service.start()
        thread.start()
        try:
            with service.condition:
                if not service.condition.wait_for(lambda:service.latest is not None, timeout=5):
                    raise RuntimeError("No frame generated")
            base = f"http://127.0.0.1:{server.server_port}"
            http = {}
            for path in ("/", "/static/app.js", "/api/status", "/api/pipeline"):
                with urllib.request.urlopen(base+path, timeout=5) as response:
                    body = response.read()
                    http[path] = {"status":response.status,"bytes":len(body)}
                    if path == "/api/status":
                        http["status_snapshot"] = json.loads(body)
            req = urllib.request.Request(base+"/capture", data=b"", method="POST")
            with urllib.request.urlopen(req, timeout=5) as response:
                capture = json.load(response)
                http["capture"] = {"status":response.status,"source":capture["metadata"]["source"]}
            with urllib.request.urlopen(base+capture["url"], timeout=5) as response:
                assert response.read(2) == b"\xff\xd8"
                http["jpeg"] = {"status":response.status,"signature":"ffd8"}
            for path in ("/video_feed", "/events"):
                with urllib.request.urlopen(base+path, timeout=5) as response:
                    http[path] = {"status":response.status,"content_type":response.headers["Content-Type"],
                                  "prefix":response.read(30).decode(errors="replace")}
            (evidence/"http-check.json").write_text(json.dumps(http,ensure_ascii=False,indent=2),encoding="utf-8")
        finally:
            server.shutdown()
            service.close()
            thread.join(timeout=5)
    (evidence/"validation.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(output.getvalue())
    print("Actual HTTP, MJPEG, capture, SSE: passed")
    if not result.wasSuccessful():
        raise SystemExit(1)


if __name__ == "__main__":
    main()
