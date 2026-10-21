"""D01~D12: 함수·중첩 복사·짝짓기·CSV/JSON·중복·집계·모듈 실습."""
import argparse
from copy import deepcopy
import csv
import io
import json
import math
from pathlib import Path
import tempfile


def normalize(raw):
    if raw is None or not raw.strip():return None
    value=float(raw)
    if not math.isfinite(value):raise ValueError('유한 숫자가 아님')
    return value


def group(records):
    result={}
    for record in records:
        bucket=result.setdefault(record['area'],[])
        if record['value'] is not None:bucket.append(record['value'])
    return {key:{'count':len(values),'sum':sum(values),'average':sum(values)/len(values) if values else None} for key,values in result.items()}


def demonstrate():
    result={}
    def corrected(value,offset=1):return value+offset
    result['D01']={'returned':corrected(22.5)}
    outer=10
    def scoped(outer=3):return outer+1
    result['D02']={'default':scoped(),'keyword':scoped(outer=8),'outer_unchanged':outer}
    original=[{'readings':[1,2]}];shallow=original.copy();deep=deepcopy(original)
    shallow[0]['readings'].append(3);deep[0]['readings'].append(4)
    result['D03']={'original_after_shallow_edit':original,'independent_deep_copy':deep}
    names=['camera','mic','kit'];counts=[2,3]
    result['D04']={'enumerate':list(enumerate(names,1)), 'zip':list(zip(names,counts)), 'length_mismatch':len(names)!=len(counts)}
    parsed=[]
    for raw in ['22.5','','0','bad','NaN']:
        try:parsed.append({'raw':raw,'value':normalize(raw),'error':None})
        except ValueError:parsed.append({'raw':raw,'value':None,'error':'잘못된 숫자'})
    result['D05']=parsed
    text='id,area,value\n001,A,22.5\n002,A,0\n003,B,\n'
    with tempfile.TemporaryDirectory() as folder:
        root=Path(folder);source=root/'input.csv';source.write_text(text,encoding='utf-8')
        with source.open(encoding='utf-8',newline='') as handle:rows=list(csv.DictReader(handle))
        result['D06']={'rows':len(rows),'first_value_type':type(rows[0]['value']).__name__}
        output=root/'output.csv'
        with output.open('w',encoding='utf-8',newline='') as handle:
            writer=csv.DictWriter(handle,fieldnames=['id','area','value']);writer.writeheader();writer.writerows(rows)
        with output.open(encoding='utf-8',newline='') as handle:restored=list(csv.DictReader(handle))
        assert restored==rows
        result['D07']={'csv_round_trip':restored==rows,'identifier':restored[0]['id']}
        records=[{**row,'value':normalize(row['value']),'active':True} for row in rows]
        report_path=root/'report.json';report_path.write_text(json.dumps(records,ensure_ascii=False,allow_nan=False),encoding='utf-8')
        assert json.loads(report_path.read_text())==records
        result['D08']={'json_round_trip':True,'records':records}
    seen=set();accepted=[];issues=[]
    for row in [{'id':'001'},{'id':''},{'id':'001'},{'id':'002'}]:
        if not row['id']:issues.append('번호 누락')
        elif row['id'] in seen:issues.append('번호 중복')
        else:accepted.append(row);seen.add(row['id'])
    result['D09']={'accepted':accepted,'issues':issues}
    result['D10']=group(records)
    from sensor_pipeline import classify
    result['D11']={'imported_module':'sensor_pipeline','imported_result':classify('0')}
    result['D12']={'flow':['CSV 읽기','변환','누락/중복 검사','구역 집계','JSON 저장'],'report':group(records)}
    assert result['D03']['original_after_shallow_edit'][0]['readings']==[1,2,3]
    assert result['D10']['B']['average'] is None
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('concept',nargs='?');args=parser.parse_args()
    results=demonstrate()
    if args.concept:
        if args.concept not in results:parser.error('D01~D12 중에서 선택하세요.')
        results={args.concept:results[args.concept]}
    print(json.dumps(results,ensure_ascii=False,indent=2))
