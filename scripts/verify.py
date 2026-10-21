"""전체 실습을 실행하고 원본 입력을 보존한 실제 검사 기록을 남긴다."""
from datetime import datetime, timezone
import csv
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT
EVIDENCE = ROOT / 'evidence'


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')


def execute(path, text='', *args):
    result = subprocess.run([sys.executable, str(path), *map(str,args)], cwd=REPO, input=text,
                            capture_output=True, text=True, timeout=15)
    return {'file':str(path.relative_to(ROOT)), 'returncode':result.returncode, 'stdout':result.stdout,
            'stderr':result.stderr.replace(str(REPO),'<REPOSITORY>')}


def run():
    EVIDENCE.mkdir(exist_ok=True)
    checks=[]
    data_files=list((ROOT/'labs').glob('*/data/*.csv'))
    originals={str(path.relative_to(ROOT)):hashlib.sha256(path.read_bytes()).hexdigest() for path in data_files}
    debug=[]
    base=ROOT/'labs/2026-10-14/work'
    for index in range(1,19):
        key=f'A{index:02}'
        normal,broken,fixed,extra=[execute(base/f'{key}_{suffix}.py') for suffix in ['normal','broken','fixed','extra']]
        assert normal['returncode']==fixed['returncode']==extra['returncode']==0, key
        assert normal['stdout']==fixed['stdout'],key+' fixed differs'
        assert broken['returncode']!=0 or broken['stdout']!=normal['stdout'],key+' broken was not reproduced'
        debug.append({'activity':key,'normal':normal,'broken':broken,'fixed':fixed,'extra':extra})
    write_json(EVIDENCE/'debug-results.json',debug)
    print('Python 기초 디버깅 18개 × 4종 실행 성공',flush=True)
    advanced=[]
    base=ROOT/'labs/2026-10-15/work'
    for index in range(1,19):
        row=execute(base/f'A{index:02}_example.py')
        assert row['returncode']==0,row
        advanced.append(row)
    write_json(EVIDENCE/'advanced-results.json',advanced)
    print('Python 심화 18개 활동 실행 성공',flush=True)
    data_checks=[]
    base=ROOT/'labs/2026-10-08/work'
    for path in sorted(base.glob('*.csv')):
        with path.open(encoding='utf-8-sig',newline='') as handle:rows=list(csv.reader(handle,strict=True))
        assert rows and all(len(row)==len(rows[0]) for row in rows[1:]),path
        data_checks.append({'file':str(path.relative_to(ROOT)),'columns':len(rows[0]),'records':len(rows)-1,'valid':True})
    for path in sorted(base.glob('*.json')):
        value=json.loads(path.read_text(encoding='utf-8'))
        data_checks.append({'file':str(path.relative_to(ROOT)),'root_type':type(value).__name__,'valid':True})
    fixed=list(csv.DictReader((base/'A23_fixed.csv').open(encoding='utf-8')))
    assert fixed[3]['temperature_c']=='0.0' and fixed[2]['temperature_c']==''
    fixed_json=json.loads((base/'A23_fixed.json').read_text())
    assert fixed_json[1]['temperature_c'] is None and type(fixed_json[1]['active']) is bool
    keys=[(row['sensor_id'],row['measured_at']) for row in fixed]
    assert len(keys)==len(set(keys))==6
    for filename in ['A07_types.py','A11_structures.py']:
        record=execute(base/filename);assert record['returncode']==0,record
        data_checks.append(record)
    write_json(EVIDENCE/'data-check.json',data_checks)
    for filename in ['basic_concepts.py','advanced_concepts.py']:
        result=execute(ROOT/'examples'/filename)
        assert result['returncode']==0,result
        write_json(EVIDENCE/filename.replace('.py','.json'),json.loads(result['stdout']))
    for name in ['basic','advanced']:
        sys.path.insert(0,str(ROOT/'examples'))
    suites=[]
    for directory,pattern in [(ROOT/'tests','test_*.py'),(ROOT/'projects/equipment-loan','test_*.py')]:
        sys.path.insert(0,str(directory))
        suite=unittest.defaultTestLoader.discover(str(directory),pattern=pattern,top_level_dir=str(directory))
        stream=io.StringIO();result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
        suites.append({'directory':str(directory.relative_to(ROOT)),'count':result.testsRun,'success':result.wasSuccessful(),
                       'log':stream.getvalue().replace(str(REPO),'<REPOSITORY>')})
        assert result.wasSuccessful(),stream.getvalue()
    # Save actual homework products, keeping state-changing reservation runs in temporary tests.
    for filename in ['AH01_shapes.py','AH03_sensor_report.py']:
        result=execute(ROOT/'assignments/advanced'/filename);assert result['returncode']==0,result
        checks.append(result)
    for filename in ['git_practice.py']:
        result=execute(ROOT/'scripts'/filename);assert result['returncode']==0,result
        checks.append(result)
    result=execute(ROOT/'mcp/client_demo.py');assert result['returncode']==0,result;checks.append(result)
    equipment=execute(ROOT/'projects/equipment-loan/app.py','','list')
    assert equipment['returncode']==0,equipment
    write_json(EVIDENCE/'equipment-cli.json',equipment)
    for path in data_files:
        assert originals[str(path.relative_to(ROOT))]==hashlib.sha256(path.read_bytes()).hexdigest(),path
    report={'checked_at':datetime.now(timezone.utc).isoformat(),'python':sys.version.split()[0],
            'unit_suites':suites,'python_test_count':sum(row['count'] for row in suites),
            'debug_activity_count':len(debug),'debug_script_runs':len(debug)*4,'advanced_activity_count':len(advanced),
            'data_outputs_checked':len(data_checks),'concept_examples':{'basic':17,'advanced':12},
            'original_inputs_unchanged':True,'commands':checks,'result':'passed',
            'external_pending':['Notion actual authorized page read','human team review','user PC GitHub Desktop installation/login']}
    write_json(EVIDENCE/'validation.json',report)
    print(json.dumps({k:v for k,v in report.items() if k not in ['unit_suites','commands']},ensure_ascii=False,indent=2),flush=True)
    return report


if __name__=='__main__':
    run()
