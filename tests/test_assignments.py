import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


shapes = module('shapes', 'assignments/advanced/AH01_shapes.py')
seats = module('persistent', 'assignments/advanced/AH02_persistent_seats.py')
sensors = module('sensors', 'assignments/advanced/AH03_sensor_report.py')
basic_seats = module('basic_seats', 'assignments/basic/HW02_seats.py')


def cli(path, text='', *arguments):
    return subprocess.run([sys.executable, str(ROOT / path), *map(str, arguments)], input=text,
                          capture_output=True, text=True, timeout=10)


class AssignmentTest(unittest.TestCase):
    def test_all_official_basic_examples(self):
        catalog = json.loads((ROOT / 'curriculum.json').read_text())
        tasks = next(row['assignments'] for row in catalog if row['date'] == '2026-10-14')
        files = ['HW01_tree.py', 'HW02_seats.py', 'HW03_measurements.py']
        for task, filename in zip(tasks, files):
            for input_text, expected in task['examples']:
                with self.subTest(task=task['id'], input=input_text):
                    result = cli('assignments/basic/' + filename, input_text)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertEqual(result.stdout, expected)

    def test_tree_retries_and_upper_boundary(self):
        result = cli('assignments/basic/HW01_tree.py', '3.1\n16\n15\n')
        lines = result.stdout.splitlines()
        self.assertEqual(lines[:2], ['높이 오류'] * 2)
        self.assertEqual(len(lines[2:]), 16)
        self.assertEqual(lines[-2], '*' * 29)
        self.assertTrue(all(row == row.rstrip() for row in lines))

    def test_basic_seat_failed_operations_preserve_state(self):
        state = [False] * 5
        for number in [0, 6, True]:
            self.assertEqual(basic_seats.change(state, number, True), '좌석 오류')
            self.assertEqual(state, [False] * 5)
        basic_seats.change(state, 3, True)
        before = state.copy()
        self.assertEqual(basic_seats.change(state, 3, True), '이미 예약')
        self.assertEqual(state, before)

    def test_measurements_errors_negative_and_equal_threshold(self):
        result = cli('assignments/basic/HW03_measurements.py', 'bad\n1001\n-2\n-2\n-3\n0\n1001\n DoNe \n')
        self.assertEqual(result.stdout, '기준 오류\n기준 오류\n입력 오류\n개수 3\n합계 -5\n평균 -1.67\n최댓값 0\n최솟값 -3\n기준 초과 1\n')

    def test_shape_both_types_all_required_heights(self):
        for shape in ['tree', 'diamond']:
            for height in [3, 4, 15]:
                with self.subTest(shape=shape, height=height):
                    lines = shapes.make_lines({'shape': shape, 'height': height, 'char': '#'})
                    self.assertEqual(len(lines), height + 1 if shape == 'tree' else height * 2 - 1)
                    self.assertEqual(lines[height-1], '#' * (2*height-1))
                    self.assertTrue(all(line == line.rstrip() for line in lines))
                    if shape == 'diamond':
                        self.assertEqual(lines, list(reversed(lines)))

    def test_bad_shape_settings_preserve_existing_output(self):
        invalid = [True, [], {}, {'shape':'tree','height':True,'char':'*'}, {'shape':'tree','height':3.0,'char':'*'},
                   {'shape':'bad','height':3,'char':'*'}, {'shape':'tree','height':3,'char':'xx'},
                   {'shape':[],'height':3,'char':'*'}, {'shape':'tree','height':3,'char':[]}]
        with tempfile.TemporaryDirectory() as folder:
            source, output = Path(folder)/'shape.json', Path(folder)/'shape.txt'
            output.write_text('DO NOT OVERWRITE\n')
            for value in invalid:
                source.write_text(json.dumps(value))
                result = cli('assignments/advanced/AH01_shapes.py', '', '--config', source, '--output', output)
                self.assertEqual(result.stdout, '설정 오류\n')
                self.assertEqual(output.read_text(), 'DO NOT OVERWRITE\n')
            for text in ['{bad', '']:
                source.write_text(text)
                self.assertEqual(cli('assignments/advanced/AH01_shapes.py','', '--config',source,'--output',output).stdout,'설정 오류\n')
                self.assertEqual(output.read_text(),'DO NOT OVERWRITE\n')

    def test_persistent_seats_two_separate_processes(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'seats.json'
            self.assertEqual(cli('assignments/advanced/AH02_persistent_seats.py','2\n3\n0\n','--state',path).stdout, '예약 완료\n종료\n')
            result = cli('assignments/advanced/AH02_persistent_seats.py','1\n3\n3\n0\n','--state',path)
            self.assertEqual(result.stdout, '1:O 2:O 3:X 4:O 5:O\n취소 완료\n종료\n')
            self.assertEqual(json.loads(path.read_text()), [False]*5)

    def test_bad_state_file_preserved(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'seats.json'
            for text in ['broken', '[false,false,false,false]', '[0,1,0,0,0]', '["false",false,false,false,false]', '{}']:
                path.write_text(text)
                result = cli('assignments/advanced/AH02_persistent_seats.py','0\n','--state',path)
                self.assertEqual(result.stdout, '저장파일 오류\n')
                self.assertEqual(path.read_text(), text)

    def test_sensor_official_report(self):
        header, rows = sensors.read_rows(ROOT/'assignments/advanced/data/sensors.csv')
        report = sensors.aggregate(header, rows)
        self.assertEqual((report['input_count'],report['accepted_count'],report['measured_count'],report['missing_count']), (6,3,2,1))
        self.assertEqual(report['average'], 26.25)
        self.assertEqual(report['alerts'], ['S02'])
        self.assertIsNone(report['areas']['B']['average'])
        self.assertEqual(report['issues'], [{'line':5,'reason':'번호 중복'},{'line':6,'reason':'온도 오류'},{'line':7,'reason':'번호 누락'}])

    def test_sensor_validation_order_and_reuse_after_failed_row(self):
        header = ['id','area','temperature']
        rows = [['X','A','bad'],['X','A','0'],['X','', 'bad'],['X','A','NaN'],['Y','A'],['','', 'bad'],['Y','B','Infinity'],['Y','B','']]
        report = sensors.aggregate(header, rows)
        self.assertEqual(report['accepted_count'], 2)
        self.assertEqual(report['average'], 0.0)
        self.assertEqual([issue['reason'] for issue in report['issues']], ['온도 오류','구역 누락','번호 중복','열 개수 오류','번호 누락','온도 오류'])

    def test_sensor_missing_header_preserves_report(self):
        with tempfile.TemporaryDirectory() as folder:
            source, output = Path(folder)/'bad.csv', Path(folder)/'report.json'
            output.write_text('OLD')
            source.write_text('id,temperature\nA,22\n')
            result = cli('assignments/advanced/AH03_sensor_report.py','','--source',source,'--output',output)
            self.assertEqual(result.stdout, '입력파일 오류\n')
            self.assertEqual(output.read_text(),'OLD')


if __name__ == '__main__':
    unittest.main()
