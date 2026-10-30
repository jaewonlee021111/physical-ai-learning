import io
import threading
import zipfile
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from fastapi.testclient import TestClient
from PIL import Image
import collector

def test_camera_capture_delete_class_zip(tmp_path,monkeypatch):
    payload=io.BytesIO()
    Image.new("RGB",(10,8),"red").save(payload,format="JPEG")
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200);self.end_headers();self.wfile.write(payload.getvalue())
        def log_message(self,*args):
            pass
    server=ThreadingHTTPServer(("127.0.0.1",0),Handler)
    t=threading.Thread(target=server.serve_forever,daemon=True);t.start()
    monkeypatch.setattr(collector,"ROOT",tmp_path)
    monkeypatch.setattr(collector,"CAPTURE_URL",f"http://127.0.0.1:{server.server_port}/capture")
    try:
        with TestClient(collector.app) as c:
            r=c.post("/classes/cola/capture");assert r.status_code==201
            name=r.json()["name"]
            assert c.get("/classes/cola").json()["photos"]==[name]
            with zipfile.ZipFile(io.BytesIO(c.get("/download/cola").content)) as z:
                assert z.namelist()==["cola/"+name]
            assert c.get("/classes/cola/"+name).status_code==200
            assert c.delete("/classes/cola/"+name).status_code==204
            assert c.get("/classes/cola").json()["photos"]==[]
            assert c.post("/classes/bad.name/capture").status_code==422
    finally:
        server.shutdown();server.server_close();t.join()

def test_no_camera_is_not_success(tmp_path,monkeypatch):
    monkeypatch.setattr(collector,"ROOT",tmp_path)
    monkeypatch.setattr(collector,"CAPTURE_URL","")
    with TestClient(collector.app) as c:
        assert c.post("/classes/cola/capture").status_code==503
