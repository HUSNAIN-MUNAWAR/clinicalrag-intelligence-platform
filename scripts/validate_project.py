import subprocess, sys, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
checks=[]
def run(name, cmd, cwd=ROOT):
    p=subprocess.run(cmd,cwd=cwd,text=True,capture_output=True)
    checks.append({'name':name,'ok':p.returncode==0,'stdout':p.stdout[-2000:],'stderr':p.stderr[-2000:]})
    return p.returncode==0
run('python_compile',[sys.executable,'-m','compileall','-q','backend/app'])
run('backend_tests',[sys.executable,'-m','pytest','-q','backend/tests'])
print(json.dumps(checks, indent=2))
if not all(c['ok'] for c in checks): sys.exit(1)
