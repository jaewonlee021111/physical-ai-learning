"""네트워크 없이 실제 Git 저장소로 commit·branch·merge·충돌·fetch·push를 연습."""
import json
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def practice():
    transcript = []
    with tempfile.TemporaryDirectory() as folder:
        root = Path(folder)
        first, second, remote = root/'first', root/'second', root/'remote.git'
        first.mkdir()
        def git(cwd, *args, expected=0):
            result = subprocess.run(['git', *args], cwd=cwd, capture_output=True, text=True, timeout=10)
            transcript.append({'command':['git',*args], 'cwd':Path(cwd).name, 'returncode':result.returncode,
                               'stdout':result.stdout.replace(str(root),'<TEMP>'), 'stderr':result.stderr.replace(str(root),'<TEMP>')})
            if result.returncode != expected:
                raise AssertionError(result.stderr)
            return result
        git(first,'init','-b','main')
        git(first,'config','user.name','Physical AI local practice')
        git(first,'config','user.email','practice@example.invalid')
        (first/'README.md').write_text('base\n')
        git(first,'add','README.md');git(first,'commit','-m','initial practice')
        git(first,'switch','-c','feature')
        (first/'README.md').write_text('feature improvement\n')
        git(first,'add','README.md');git(first,'commit','-m','feature change')
        git(first,'switch','main')
        (first/'README.md').write_text('main change\n')
        git(first,'diff');git(first,'add','README.md');git(first,'diff','--cached')
        git(first,'commit','-m','main change')
        git(first,'merge','feature',expected=1)
        assert '<<<<<<<' in (first/'README.md').read_text()
        (first/'README.md').write_text('main and feature reconciled\n')
        git(first,'add','README.md');git(first,'commit','-m','resolve conflict')
        git(root,'init','--bare','--initial-branch=main',str(remote))
        git(first,'remote','add','origin',str(remote));git(first,'push','-u','origin','main')
        git(root,'clone',str(remote),str(second))
        (first/'CHANGELOG.md').write_text('second local change\n')
        git(first,'add','CHANGELOG.md');git(first,'commit','-m','add changelog');git(first,'push')
        git(second,'fetch','origin');git(second,'pull','--ff-only')
        assert (second/'CHANGELOG.md').read_text() == 'second local change\n'
        git(second,'log','--oneline','--graph','--all')
        git(second,'status','--short')
        # Bare remote is local, no GitHub credentials or third-party accounts involved.
        for record in transcript:
            record['command'] = [value.replace(str(root),'<TEMP>') for value in record['command']]
    report={'scope':'isolated local Git and bare remote, not a human peer review', 'steps':transcript,'result':'passed'}
    path=ROOT/'evidence/git-transcript.json';path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return report


if __name__=='__main__':
    print(f"Git 실제 작업 {len(practice()['steps'])}개 완료")
