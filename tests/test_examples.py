import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "examples"))
from tree import render_tree
from sensor_pipeline import classify, convert


class ExamplesTest(unittest.TestCase):
    def test_tree_shape(self):
        self.assertEqual(render_tree(3), "  *\n ***\n*****\n  *")
        self.assertEqual(render_tree(1, 2), "*   *\n*   *")
        with self.assertRaises(ValueError):
            render_tree(0)

    def test_missing_invalid_and_boundaries(self):
        for raw in ["", " ", None]:
            self.assertEqual(classify(raw), (None, "미측정"))
        for raw in ["oops", "NaN", "inf", "-inf"]:
            self.assertEqual(classify(raw), (None, "잘못된 숫자"))
        for raw in ["0", "35"]:
            self.assertEqual(classify(raw)[1], "정상")
        for raw in ["-0.01", "35.01"]:
            self.assertEqual(classify(raw)[1], "범위 밖")

    def test_round_trip_and_identifier(self):
        source = Path(__file__).resolve().parents[1] / "data" / "readings.csv"
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / "nested" / "report.json"
            report = convert(source, output)
            self.assertEqual(json.loads(output.read_text(encoding="utf-8")), report)
            self.assertEqual(report["records"][0]["sensor_id"], "001")
            self.assertEqual(report["count"], 6)
            self.assertEqual(report["normal_count"], 3)
            self.assertAlmostEqual(report["normal_mean"], 56 / 3)

    def test_empty_and_bad_csv(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "input.csv"
            output = Path(folder) / "report.json"
            source.write_text("sensor_id,timestamp,value,unit\n", encoding="utf-8")
            self.assertIsNone(convert(source, output)["normal_mean"])
            source.write_text("wrong,header\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                convert(source, output)


if __name__ == "__main__":
    unittest.main()

