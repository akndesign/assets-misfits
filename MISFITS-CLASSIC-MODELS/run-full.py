from pathlib import Path
import subprocess,sys,shutil,json,time
O=Path(__file__).resolve().parent
if shutil.disk_usage(O).free<35_000_000_000:raise SystemExit('Need 35GB free before the full render starts')
with (O/'full-run.log').open('a') as log:
 code=subprocess.call(['/Applications/Blender.app/Contents/MacOS/Blender','-b','-t','2','--python',str(O/'render.py'),'--','--full'],stdout=log,stderr=subprocess.STDOUT)
 if code:raise SystemExit(code)
 code=subprocess.call([sys.executable,str(O/'encode.py')],stdout=log,stderr=subprocess.STDOUT)
 if code:
  (O/'status.json').write_text(json.dumps({'phase':'Encoding or verification failed','completed':305,'total':305,'error':'Inspect full-run.log; image sequence retained'}));raise SystemExit(code)
