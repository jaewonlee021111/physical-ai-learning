"""장치 없는 서버 검사. 실제 YOLO 검증은 step6 별도 결과를 확인한다."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import cv2
import numpy as np
from app import CameraService, create_app
from pipeline import MODES, as_bgr, preprocess, process, synthetic_frame
import stages


class VisionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.service = CameraService(runtime=Path(self.temp.name))
        self.client = create_app(self.service).test_client()

    def tearDown(self):
        self.service.close()
        self.temp.cleanup()

    def ready(self):
        self.service.start()
        with self.service.condition:
            self.assertTrue(self.service.condition.wait_for(lambda: self.service.latest is not None, timeout=5))

    def test_rgb_roundtrip_and_pixel_order(self):
        frame = np.full((2, 2, 3), [7, 50, 200], dtype=np.uint8)
        rgb = preprocess(frame, "rgb")
        self.assertEqual(rgb[0, 0].tolist(), [200, 50, 7])
        np.testing.assert_array_equal(as_bgr(rgb, "rgb"), frame)

    def test_all_modes_encode_and_gray_shape(self):
        for mode in MODES:
            with self.subTest(mode=mode):
                encoded, info = process(synthetic_frame(), mode)
                decoded = cv2.imdecode(np.frombuffer(encoded, np.uint8), cv2.IMREAD_COLOR)
                self.assertEqual(decoded.shape, (360, 640, 3))
                self.assertFalse(info["inference_enabled"])
        self.assertEqual(preprocess(synthetic_frame(), "gray").ndim, 2)

    def test_invalid_mode(self):
        with self.assertRaises(ValueError):
            preprocess(synthetic_frame(), "invalid")

    def test_capture_without_frame_is_503(self):
        self.assertEqual(self.client.post("/capture").status_code, 503)

    def test_capture_and_metadata_and_gallery(self):
        self.ready()
        result = self.client.post("/capture")
        self.assertEqual(result.status_code, 200)
        payload = result.get_json()
        self.assertEqual(payload["metadata"]["source"], "synthetic")
        with self.client.get(payload["url"]) as image_response:
            self.assertEqual(image_response.mimetype, "image/jpeg")
        self.assertIn(payload["url"], self.client.get("/api/captures").get_json())
        metadata_path = next((Path(self.temp.name)/"captures").glob("*.json"))
        self.assertEqual(json.loads(metadata_path.read_text())["source"], "synthetic")

    def test_unique_capture_names(self):
        self.ready()
        urls = [self.client.post("/capture").get_json()["url"] for _ in range(4)]
        self.assertEqual(len(set(urls)), 4)

    def test_capture_path_traversal_rejected(self):
        outside = Path(self.temp.name)/"secret.txt"
        outside.write_text("not public")
        self.assertEqual(self.client.get("/captures/../secret.txt").status_code, 404)

    def test_settings_valid_and_invalid(self):
        response = self.client.post("/api/settings", json={"mode":"gray", "confidence":.8, "infer_every":2})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.service.mode, "gray")
        for payload in [[], None, {"mode":"oops"}, {"confidence":2}, {"infer_every":0}, {"confidence":"nan"}]:
            self.assertEqual(self.client.post("/api/settings", json=payload).status_code, 400)

    def test_mjpeg_two_clients_share_producer(self):
        self.ready()
        first = self.client.get("/video_feed", buffered=False)
        second = create_app(self.service).test_client().get("/detect_feed", buffered=False)
        try:
            self.assertIn("multipart/x-mixed-replace", first.content_type)
            self.assertTrue(next(first.response).startswith(b"--frame\r\nContent-Type: image/jpeg"))
            self.assertTrue(next(second.response).startswith(b"--frame"))
        finally:
            first.close()
            second.close()

    def test_sse_and_xml_metadata(self):
        self.ready()
        response = self.client.get("/events", buffered=False)
        try:
            payload = next(response.response).decode()
            data = json.loads(payload.removeprefix("data: ").strip())
            self.assertEqual(data["source"], "synthetic")
        finally:
            response.close()
        metadata = self.client.get("/api/pipeline").get_json()
        self.assertEqual({row["id"] for row in metadata}, {"capture","preprocess","inference","postprocess","visualize","output"})
        self.assertTrue(all(row.get("reason") for row in metadata))

    def test_failed_camera_released_and_no_fake_fallback(self):
        with patch("app.cv2.VideoCapture") as constructor:
            cap = constructor.return_value
            cap.isOpened.return_value = False
            broken = CameraService(source="camera", runtime=Path(self.temp.name)/"broken")
            broken.start()
            broken.thread.join(timeout=3)
            try:
                self.assertIn("unavailable", broken.error)
                self.assertIsNone(broken.latest)
                cap.release.assert_called_once()
            finally:
                broken.close()

    def test_sampling_reuses_boxes_and_marks_skip(self):
        class StubDetector:
            device = "cpu"
            size = 320
            calls = 0
            def detect(self, frame, confidence):
                self.calls += 1
                return [{"label":"test fixture", "confidence":.9, "xyxy":[20,20,50,50]}]
        detector = StubDetector()
        self.service.detector = detector
        self.service.infer_every = 3
        self.ready()
        with self.service.condition:
            self.service.condition.wait_for(lambda: self.service.status.get("frame", 0) >= 2, timeout=3)
            self.assertTrue(self.service.status["sampled_out"])
            self.assertEqual(self.service.status["detections"][0]["label"], "test fixture")
        self.assertEqual(detector.calls, 1)

    def test_window_cli_rejects_zero_skip_and_size(self):
        import contextlib
        import io
        from step7_realtime_yolo import main
        for option in ("--skip", "--imgsz"):
            with patch("sys.argv", ["step7", option, "0", "--no-yolo"]):
                with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
                    main()
                self.assertEqual(error.exception.code, 2)

    def test_pc_check_reports_missing_camera_and_releases_it(self):
        from pc_check import camera_check
        with patch("pc_check.cv2.VideoCapture") as constructor:
            constructor.return_value.isOpened.return_value = False
            self.assertEqual(camera_check(1), {"status":"unavailable","index":1})
            constructor.return_value.release.assert_called_once()

    def test_pc_check_reads_real_camera_interface_without_synthetic_fallback(self):
        from pc_check import camera_check
        with patch("pc_check.cv2.VideoCapture") as constructor:
            cap = constructor.return_value
            cap.isOpened.return_value = True
            cap.read.return_value = (True,np.zeros((48,64,3),dtype=np.uint8))
            result = camera_check(2,frame_count=3)
            self.assertEqual(result["status"],"passed")
            self.assertEqual(result["frames_read"],3)
            self.assertEqual(cap.read.call_count,3)
            cap.release.assert_called_once()


if __name__ == "__main__":
    unittest.main(verbosity=2)

