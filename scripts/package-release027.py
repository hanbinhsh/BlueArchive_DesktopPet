from pathlib import Path
import zipfile,hashlib,json
r=Path('.');base=r/'release/v0.2.7/win-unpacked';out=r/'release/BA-Desktop-Pet-0.2.7-win-x64.zip'
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for p in sorted(base.rglob('*')):
  if p.is_file():z.write(p,p.relative_to(base))
with zipfile.ZipFile(out) as z:
 assert z.testzip() is None
 for n in z.namelist():assert hashlib.sha256(z.read(n)).digest()==hashlib.sha256((base/n).read_bytes()).digest(),n
 count=len(z.namelist())
source=r/'release/BA-Desktop-Pet-0.2.7-source.zip'
with zipfile.ZipFile(source,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for folder in ['src','scripts','tests','docs','native']:
  for p in (r/folder).rglob('*'):
   if p.is_file() and '__pycache__' not in p.parts and 'bin' not in p.parts:z.write(p,p)
 for name in ['package.json','package-lock.json','tsconfig.json','README.md']:z.write(r/name,name)
 for p in (r/'test-results').glob('*.json'):
  if p.name.startswith(('visual-repair','furniture-update','furniture-retry','hiyori-furniture','update027','release027','outline-runtime','cafe-fx-adaptation','furniture-review-1029','prop-review-1029','timeline-preroll-1029','racing-halo','neru-inversebind-1029')):z.write(p,'validation/'+p.name)
 z.writestr('SOURCE-SETUP.md','Run npm ci, copy resources/characters from the portable package into characters/, then npm run build. Acquisition caches are not included. See docs/UPDATE-027.md for verification and outstanding work.')
with zipfile.ZipFile(source) as z:assert z.testzip() is None
report={'portable':{'path':str(out),'bytes':out.stat().st_size,'files':count,'sha256':hashlib.sha256(out.read_bytes()).hexdigest()},'source':{'path':str(source),'bytes':source.stat().st_size,'sha256':hashlib.sha256(source.read_bytes()).hexdigest()}}
(r/'test-results/release027.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
