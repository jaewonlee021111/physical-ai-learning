"""본인 포트를 명시해 모니터·RGB·KST 시계 동기화를 수행한다."""
import argparse
from datetime import datetime,timezone,timedelta
import time


def command(mode,values=None,timestamp=None):
    """<summary>장치에 보낼 한 줄 명령을 만든다.</summary><param name="mode">rgb 또는 clock</param><param name="values">RGB 세 값</param><param name="timestamp">UTC Unix 초</param><input>사용자 설정</input><output>ASCII 명령</output><reason>PC의 현재 시각과 UNO 시간을 명시적으로 동기화한다.</reason>"""
    if mode=='rgb':
        if not values or len(values)!=3 or any(type(v) is not int or not 0<=v<=255 for v in values):
            raise ValueError('RGB: three integers 0..255')
        return ('RGB '+' '.join(map(str,values))+'\n').encode('ascii')
    if mode=='clock':
        stamp=int(time.time() if timestamp is None else timestamp)
        if not 1704067200<=stamp<=4102444800:
            raise ValueError('Timestamp outside 2024..2100')
        return f'TIME {stamp}\n'.encode('ascii')
    raise ValueError('Unknown command')


def main():
    """<summary>선택한 UNO를 열어 명령과 로그를 주고받는다.</summary><input>명령행 인수</input><output>터미널 출력</output><reason>다른 장치에 임의로 연결하지 않고 사용자가 지정한 포트만 연다.</reason>"""
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port',required=True)
    parser.add_argument('mode',choices=['monitor','rgb','clock'])
    parser.add_argument('rgb',type=int,nargs='*')
    args=parser.parse_args()
    import serial
    with serial.Serial(args.port,115200,timeout=1) as device:
        time.sleep(2) # UNO는 시리얼 포트를 열 때 재시작할 수 있다.
        if args.mode!='monitor':
            device.write(command(args.mode,args.rgb))
            if args.mode=='clock':
                print('PC KST:',datetime.now(timezone(timedelta(hours=9))).isoformat(timespec='seconds'))
        try:
            while True:
                line=device.readline().decode('utf-8',errors='replace')
                if line:
                    print(line,end='')
        except KeyboardInterrupt:
            pass


if __name__=='__main__':
    main()
