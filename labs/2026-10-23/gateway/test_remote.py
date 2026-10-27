import io
import sys
from pathlib import Path
import tempfile
import threading
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
import unittest
import cv2
import numpy as np
from remote import RemoteReader,jpeg_packets
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"2026-10-22"/"vision"))
from app import CameraService,create_app


class RemoteTests(unittest.TestCase):
    def test_split_markers_multiple_frames_and_headers(self):
        class TinyStream(io.BytesIO):
            def read1(self,size):
                return self.read(1)
        stream=TinyStream(b"--frame\r\n\xff\xd8abc\xff\xd9\r\n--frame\r\n\xff\xd8def\xff\xd9")
        self.assertEqual(list(jpeg_packets(stream)),[b"\xff\xd8abc\xff\xd9",b"\xff\xd8def\xff\xd9"])

    def test_buffer_limit_and_truncated_input(self):
        with self.assertRaises(ValueError):
            list(jpeg_packets(io.BytesIO(b"\xff\xd8"+b"x"*20),limit=10))
        self.assertEqual(list(jpeg_packets(io.BytesIO(b"\xff\xd8partial"))),[])

    def test_rejects_file_and_embedded_credentials(self):
        for url in ["file:///etc/passwd","http://user:pass@localhost/stream","not-a-url"]:
            with self.assertRaises(ValueError):
                RemoteReader(url)

    def test_real_http_mjpeg_to_dashboard_and_capture(self):
        ok,encoded=cv2.imencode('.jpg',np.full((48,64,3),120,dtype=np.uint8))
        self.assertTrue(ok)
        jpeg=encoded.tobytes()
        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(200)
                self.send_header('Content-Type','multipart/x-mixed-replace; boundary=frame')
                self.end_headers()
                try:
                    for _ in range(10):
                        self.wfile.write(b'--frame\r\nContent-Type: image/jpeg\r\n\r\n'+jpeg+b'\r\n')
                        self.wfile.flush()
                except (BrokenPipeError,ConnectionResetError):
                    pass
            def log_message(self,*args):
                pass
        server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        threading.Thread(target=server.serve_forever,daemon=True).start()
        reader=RemoteReader(f'http://127.0.0.1:{server.server_port}/stream')
        try:
            with tempfile.TemporaryDirectory() as directory:
                service=CameraService(source='remote',reader=reader,runtime=Path(directory))
                service.start()
                try:
                    with service.condition:
                        self.assertTrue(service.condition.wait_for(lambda:service.latest is not None,timeout=4))
                    client=create_app(service).test_client()
                    info=client.get('/api/status').get_json()
                    self.assertEqual(info['source'],'remote')
                    self.assertEqual(info['shape'],[48,64,3])
                    self.assertFalse(info['model_enabled'])
                    self.assertEqual(client.post('/capture').status_code,200)
                finally:
                    service.close()
        finally:
            reader.release()
            server.shutdown()
            server.server_close()

    def test_connection_failure_is_reported(self):
        reader=RemoteReader('http://127.0.0.1:1/stream',timeout=.1)
        try:
            self.assertEqual(reader.read(),(False,None))
        finally:
            reader.release()


if __name__=='__main__':
    unittest.main(verbosity=2)
