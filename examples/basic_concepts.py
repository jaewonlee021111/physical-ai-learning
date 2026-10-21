"""C01~C17 핵심 동작을 하나씩 실행한다. JSON은 실제 함수 실행 결과다."""
import argparse
import json
from pathlib import Path
import sys


def demonstrate():
    results = {}
    results['C01'] = {'saved_file': Path(__file__).name, 'python': sys.version.split()[0]}
    results['C02'] = {'print_message': '주석은 실행하지 않고 print는 출력한다.'}
    results['C03'] = {'addition': 2+3, 'division': 7/2, 'integer_division': 7//2, 'remainder': 7%2}
    stock=8;stock=stock+3
    results['C04'] = {'stock_after_assignment': stock}
    results['C05'] = {'formatted': f'온도 {22.5:.1f}℃', 'concat': '2'+'3'}
    results['C06'] = {'raw_type': type('22').__name__, 'converted': int('22')+3}
    results['C07'] = {'normalized_command': ' DoNe '.strip().lower()}
    results['C08'] = {'equal':24==24,'exceeds':24>24,'at_least':24>=24}
    def status(value):
        if value is None:return '미측정'
        elif value > 24:return '확인'
        else:return '정상'
    results['C09'] = [status(value) for value in [None,0,24,25]]
    values=[22.5,24.0,23.5]
    results['C10'] = {'first':values[0],'last':values[-1],'count':len(values)}
    results['C11'] = {'range_1_to_3':list(range(1,4))}
    total=0;count=0
    for value in values:total+=value;count+=1
    results['C12'] = {'sum':total,'count':count,'average':total/count}
    record={'sensor_id':'S01','value':22.5}
    results['C13'] = {'id_by_key':record['sensor_id']}
    kept=[];iterator=iter(['bad','3','done','9'])
    while True:
        raw=next(iterator)
        if raw=='done':break
        if not raw.isdigit():continue
        kept.append(int(raw))
    results['C14'] = {'loop_kept':kept}
    try:int('not-a-number')
    except ValueError as error:results['C15']={'caught_error':type(error).__name__}
    def add_offset(value, offset=1):return value+offset
    results['C16'] = {'return_value':add_offset(22.5,offset=2)}
    readings=[22.5,None,0,25]
    numeric=[value for value in readings if value is not None]
    results['C17']={'count':len(readings),'measured':len(numeric),'missing':len(readings)-len(numeric),'mean':sum(numeric)/len(numeric),'status':[status(value) for value in readings]}
    assert results['C04']['stock_after_assignment']==11
    assert results['C12']['average']==70/3
    assert results['C14']['loop_kept']==[3]
    return results


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('concept',nargs='?')
    args=parser.parse_args();results=demonstrate()
    if args.concept:
        if args.concept not in results:parser.error('C01~C17 중에서 선택하세요.')
        results={args.concept:results[args.concept]}
    print(json.dumps(results,ensure_ascii=False,indent=2))
