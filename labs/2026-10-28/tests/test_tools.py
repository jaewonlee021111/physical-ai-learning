import importlib.util
import io
import json
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from dataset import audit, capture, token
from evaluate import evaluate


class DatasetTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def image(self, label, session, color):
        folder = self.root / label / session
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / "image.png"
        Image.new("RGB", (8, 6), color).save(path)
        return path

    def test_session_split(self):
        self.image("cola", "day1", "red")
        self.image("cola", "day2", "blue")
        result = audit(self.root, {"day2"})
        self.assertTrue(result["valid"])
        self.assertEqual(result["counts"], {"cola/testing": 1, "cola/training": 1})

    def test_duplicate_leakage(self):
        self.image("cola", "day1", "red")
        self.image("cola", "day2", "red")
        self.assertTrue(any("across train/test" in e for e in audit(self.root, {"day2"})["errors"]))

    def test_label_conflict(self):
        self.image("cola", "day1", "red")
        self.image("cookie", "day1", "red")
        self.assertTrue(any("conflicting" in e for e in audit(self.root, {"day2"})["errors"]))

    def test_corrupt_and_empty(self):
        p = self.image("cola", "day1", "red")
        p.write_bytes(b"not an image")
        result = audit(self.root, {"day2"})
        self.assertFalse(result["valid"])
        self.assertTrue(any("unreadable" in e for e in result["errors"]))

    def test_path_traversal(self):
        with self.assertRaises(ValueError):
            token("../private")

    def test_missing_test_session(self):
        self.image("cola", "day1", "red")
        self.assertFalse(audit(self.root, {"absent"})["valid"])

    def test_capture_over_real_local_http(self):
        buffer = io.BytesIO()
        Image.new("RGB", (10, 7), "green").save(buffer, format="JPEG")
        payload = buffer.getvalue()
        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(200)
                self.end_headers()
                self.wfile.write(payload)
            def log_message(self, *_):
                pass
        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            saved = capture(f"http://127.0.0.1:{server.server_port}/capture", self.root,
                            "background", "fixture", 2, 0)
            self.assertEqual(len(saved), 2)
            with Image.open(saved[0]) as image:
                self.assertEqual(image.size, (10, 7))
        finally:
            server.shutdown()
            server.server_close()
            thread.join()


class EvaluationTests(unittest.TestCase):
    def row(self, name, actual, a, b):
        return dict(id=name, actual=actual, scores={"cola": a, "cookie": b}, inference_ms=20)

    def test_matrix_and_macro_f1(self):
        rows = [self.row("a", "cola", .9, .1), self.row("b", "cookie", .6, .4),
                self.row("c", "cookie", .1, .9)]
        r = evaluate(rows, ["cola", "cookie"])
        self.assertEqual(r["confusion_matrix"], [[1, 0], [1, 1]])
        self.assertAlmostEqual(r["macro_f1"], 2/3)

    def test_nan_and_empty(self):
        with self.assertRaises(ValueError):
            evaluate([], ["cola", "cookie"])
        with self.assertRaises(ValueError):
            evaluate([self.row("a", "cola", float("nan"), 1)], ["cola", "cookie"])

    def test_duplicates_and_label_mismatch(self):
        row = self.row("a", "cola", .9, .1)
        with self.assertRaises(ValueError):
            evaluate([row, row], ["cola", "cookie"])
        with self.assertRaises(ValueError):
            evaluate([row], ["cola", "unknown"])

    def test_bad_probability_sum(self):
        with self.assertRaises(ValueError):
            evaluate([self.row("a", "cola", .8, .8)], ["cola", "cookie"])


if __name__ == "__main__":
    unittest.main()
