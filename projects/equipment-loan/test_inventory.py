from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from inventory import change, load, save, transact, validate


class InventoryTest(unittest.TestCase):
    def setUp(self):
        self.items = [{"id": "A", "name": "카메라", "total": 2, "available": 1}]

    def test_borrow_return_and_original(self):
        updated = change(self.items, "A", "borrow")
        self.assertEqual(updated[0]["available"], 0)
        self.assertEqual(self.items[0]["available"], 1)
        self.assertEqual(change(updated, "A", "return"), self.items)

    def test_empty_stock_and_over_return(self):
        for available, action in [(0, "borrow"), (2, "return")]:
            self.items[0]["available"] = available
            before = deepcopy(self.items)
            with self.assertRaises(ValueError):
                change(self.items, "A", action)
            self.assertEqual(self.items, before)

    def test_missing_selection(self):
        for identifier in [None, "", " ", "BAD"]:
            with self.assertRaises(ValueError):
                change(self.items, identifier, "borrow")

    def test_invalid_data(self):
        for value in [True, -1, 3, 1.5, "1"]:
            self.items[0]["available"] = value
            with self.assertRaises(ValueError):
                validate(self.items)

    def test_duplicate_id(self):
        with self.assertRaises(ValueError):
            validate(self.items * 2)

    def test_persistence_and_corruption_preservation(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "state.json"
            save(path, self.items)
            transact(path, "A", "borrow")
            self.assertEqual(load(path)[0]["available"], 0)
            before = path.read_bytes()
            with self.assertRaises(ValueError):
                transact(path, "A", "borrow")
            self.assertEqual(path.read_bytes(), before)
            path.write_text('{broken json', encoding='utf-8')
            before = path.read_bytes()
            with self.assertRaises(ValueError):
                transact(path, "A", "return")
            self.assertEqual(path.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
