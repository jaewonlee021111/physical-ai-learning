import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from types import SimpleNamespace
import cv2
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'vision'))
import pipeline
from pipeline import Pipeline
import step8_pipeline_dashboard as appmod
from readers import LatestReader,MjpegStreamReader,SyntheticReader
spec=importlib.util.spec_from_file_location('serial_console',ROOT/'tools/serial_console.py')
serial_console=importlib.util.module_from_spec(spec);spec.loader.exec_module(serial_console)


class PracticeTests(unittest.TestCase):
    def test_settings_reject_invalid_without_partial_update(self):
        settings=appmod.RuntimeSettings()
        original=settings.snapshot()
        for bad in [None,[],{'skip':True},{'skip':0},{'imgsz':321},{'conf':float('nan')},{'conf':float('inf')},{'extra':1}]:
            with self.assertRaises(ValueError):settings.update(bad)
            self.assertEqual(settings.snapshot(),original)
        self.assertEqual(settings.update({'skip':3})['skip'],3)

    def test_pipeline_accumulates_and_execution_average(self):
        p=Pipeline(window=3,log_every=1)
        p.begin_frame();p.record('inference',4);p.record('inference',6);p.end_frame()
        p.begin_frame();p.end_frame()
        row=next(x for x in p.snapshot()['stages'] if x['id']=='inference')
        self.assertEqual(row['avg_ms'],5)
        self.assertEqual(row['execution_avg_ms'],10)
        self.assertEqual(p.snapshot()['counters']['frames'],2)
        json.dumps(p.snapshot(),allow_nan=False)

    def test_abort_excludes_failed_sample(self):
        p=Pipeline();p.begin_frame();p.record('capture',5);p.abort_frame('read failed')
        self.assertEqual(p.snapshot()['counters']['aborted'],1)
        self.assertEqual(p.snapshot()['fps'],0)

    def test_log_throttle_ring_and_cursor(self):
        p=Pipeline(log_maxlen=3,log_every=5)
        p.begin_frame();p.log('INFO','hidden');p.log('WARN','skip',throttle=True)
        self.assertEqual(p.snapshot()['logs'],[])
        for i in range(5):p.log('WARN',str(i))
        self.assertEqual(len(p.snapshot()['logs']),3)
        self.assertEqual([e['seq'] for e in p.snapshot(3)['logs']],[4,5])
        self.assertTrue(p.snapshot(1)['log_gap'])
        self.assertEqual(p.snapshot(5)['logs'],[])

    def test_xml_metadata_and_parse_failure(self):
        p=Pipeline()
        @p.stage('capture')
        def valid():
            '''<summary> hello   world </summary><param name="x"> test </param>'''
            return 1
        self.assertEqual(p.metadata()[0]['summary'],'hello world')
        @p.stage('output')
        def invalid():
            '''<summary> broken & XML </summary>'''
            return 1
        self.assertIn('error',p.metadata()[-1])

    def test_latest_only_counts_drops(self):
        reader=LatestReader()
        before=pipeline.PIPELINE.snapshot()['counters']['dropped']
        reader.publish(b'one');reader.publish(b'two')
        self.assertEqual(reader.take()[0],b'two')
        self.assertEqual(pipeline.PIPELINE.snapshot()['counters']['dropped'],before+1)
        reader.close()
        with self.assertRaises(TimeoutError):reader.take(.01)

    def test_remote_url_validation(self):
        for value in ['file:///etc/passwd','http://u:p@localhost/stream','bad']:
            with self.assertRaises(ValueError):MjpegStreamReader(value)

    def test_capture_decodes_and_records_status(self):
        reader=LatestReader();ok,jpeg=cv2.imencode('.jpg',np.full((24,32,3),90,np.uint8));self.assertTrue(ok)
        reader.publish(jpeg.tobytes());pipeline.PIPELINE.begin_frame()
        frame=appmod.capture_frame(reader)
        self.assertEqual(frame.shape,(24,32,3))
        self.assertIn('decode_ms',pipeline.PIPELINE.snapshot()['status'])
        pipeline.PIPELINE.end_frame()

    def test_manual_model_timings_and_skip(self):
        result=SimpleNamespace(speed={'preprocess':1.5,'inference':7.0,'postprocess':2.0})
        detector=SimpleNamespace(predict=lambda frame,settings:result)
        pipeline.PIPELINE.begin_frame()
        self.assertIs(appmod.run_inference(detector,np.zeros((5,5,3),np.uint8),{'skip':2},1),result)
        self.assertEqual(pipeline.PIPELINE.current['inference'],7)
        pipeline.PIPELINE.end_frame()
        pipeline.PIPELINE.begin_frame()
        self.assertIsNone(appmod.run_inference(detector,None,{'skip':2},2))
        self.assertTrue(pipeline.PIPELINE.skipped)
        self.assertNotIn('inference',pipeline.PIPELINE.current)
        pipeline.PIPELINE.end_frame()

    def test_http_mjpeg_reader_processor_capture_and_reconnect(self):
        _,image=cv2.imencode('.jpg',np.full((48,64,3),100,np.uint8));jpeg=image.tobytes()
        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(200);self.send_header('Content-Type','multipart/x-mixed-replace; boundary=frame');self.end_headers()
                for _ in range(4):
                    self.wfile.write(b'--frame\r\nContent-Type: image/jpeg\r\n\r\n'+jpeg+b'\r\n');self.wfile.flush();time.sleep(.03)
            def log_message(self,*args):pass
        server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        reader=MjpegStreamReader(f'http://127.0.0.1:{server.server_port}/stream')
        processor=appmod.Processor(reader,appmod.RuntimeSettings())
        try:
            processor.start()
            with processor.store.condition:
                self.assertTrue(processor.store.condition.wait_for(lambda:processor.store.raw is not None,3))
            time.sleep(.2)
            self.assertGreater(pipeline.PIPELINE.snapshot()['counters']['reconnects'],0)
            with tempfile.TemporaryDirectory() as directory:
                client=appmod.create_app(processor,directory).test_client()
                capture=client.post('/capture').get_json()
                with client.get(capture['url']) as image_response:
                    self.assertTrue(image_response.data.startswith(b'\xff\xd8'))
                self.assertEqual(client.get('/api/captures').get_json()[0]['name'],capture['name'])
        finally:
            processor.close();server.shutdown();server.server_close();thread.join(2)
        self.assertFalse(reader.thread.is_alive());self.assertFalse(processor.thread.is_alive())

    def test_routes_settings_no_frame_and_path_escape(self):
        processor=appmod.Processor(SyntheticReader(),appmod.RuntimeSettings())
        with tempfile.TemporaryDirectory() as directory:
            client=appmod.create_app(processor,directory).test_client()
            self.assertEqual(client.get('/').status_code,200)
            self.assertEqual(client.post('/capture').status_code,503)
            self.assertEqual(client.post('/api/settings',json={'skip':True}).status_code,400)
            self.assertEqual(client.post('/api/settings',json={'skip':5}).get_json()['skip'],5)
            self.assertEqual(client.get('/captures/../../config.py').status_code,404)
            self.assertEqual(len(client.get('/api/pipeline').get_json()['stages']),6)
            first=client.get('/events',buffered=False);second=client.get('/events',buffered=False)
            self.assertEqual(first.headers['X-Accel-Buffering'],'no')
            self.assertTrue(next(first.response).startswith(b'data: '))
            self.assertTrue(next(second.response).startswith(b'data: '))
            first.close();second.close()

    def test_pc_commands_use_utc_and_rgb_bounds(self):
        self.assertEqual(serial_console.command('clock',timestamp=1800000000),b'TIME 1800000000\n')
        self.assertEqual(serial_console.command('rgb',[1,2,255]),b'RGB 1 2 255\n')
        for values in [[256,0,0],[-1,0,0],[True,0,0],[1,2]]:
            with self.assertRaises(ValueError):serial_console.command('rgb',values)


if __name__=='__main__':unittest.main()
