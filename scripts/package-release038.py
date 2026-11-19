"""Package the exact 0.2.17 program and assets verified by the current run."""
from pathlib import Path
import hashlib,json,zipfile
R=Path(__file__).resolve().parents[1];T=R/'test-results';base=R/'release/v0.2.17/win-unpacked'
def read(name):return json.loads((T/name).read_text('utf8'))
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
soak=read('release038-soak.json')
assert soak['complete'] and soak['version']=='0.2.17' and soak['elapsedSeconds']>=1800 and not soak['errors']
verified=read('release038-verification.json');assert read('release038-soak-input.json')==verified
assert sha(base/'resources/app.asar')==verified['appAsarSha256']
assert sha(base/'BA Desktop Pet.exe')==verified['executableSha256']
resources=read('release038-resources.json');assert len(resources)==599
for item in resources:
 assert sha(base/'resources/characters'/item['path'])==sha(R/'characters'/item['path'])==item['sha256']
for tag,count in [('full',145),('reported',44),('boundary',20)]:
 rows=read(f'{tag}038-runtime.json');assert len(rows)==count
 assert all(not r['diagnostics'].get('error') for r in rows)
faces=read('faces038-runtime.json');assert faces['complete'] and len(faces['results'])==16 and not faces.get('errors')
review=read('visual038-review.json');assert review['frames']==1468 and review['contactSheetsReviewed']==101 and not review['unresolvedObservedDefects']
for name in ['cloud038-runtime.json','water038-runtime.json','scroll038.json']:
 report=read(name);assert report['complete'] and not report['errors'],name
assert not read('release038-speed.json')['errors']
assert len(read('hold038.json'))==4 and len(read('transitions038.json'))==4
assert all(not x['errors'] for x in read('transitions038.json'))
assert read('menu038.json')['starCenter']=={'dx':0,'dy':0}
assert 'tests 82' in (T/'unit038.log').read_text('utf8')
assert 'Ran 26 tests' in (T/'python038.log').read_text('utf8')
package=json.loads((R/'package.json').read_text('utf8'));assert package['version']=='0.2.17'
for item in package['build']['extraFiles']:
 p=base/item['to'];p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((R/item['from']).read_bytes())
out=R/'release/BA-Desktop-Pet-0.2.17-win-x64.zip';source=R/'release/BA-Desktop-Pet-0.2.17-source.zip'
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for p in sorted(base.rglob('*')):
  if p.is_file():z.write(p,p.relative_to(base))
with zipfile.ZipFile(out) as z:
 assert z.testzip() is None
 for name in z.namelist():
  with z.open(name) as f:assert hashlib.file_digest(f,'sha256').hexdigest()==sha(base/name),name
evidence=['release038-soak.json','release038-soak-input.json','release038-resource-summary.json','release038-verification.json','release038-resources.json','resources038-installed.json','stage038-verification.json','visual038-review.json','full038-runtime.json','reported038-runtime.json','boundary038-runtime.json','faces038-runtime.json','release038-speed.json','water038-runtime.json','cloud038-runtime.json','hold038.json','transitions038.json','menu038.json','scroll038.json','unit038.log','python038.log','type038.log','build038.log','assets038.log','static038-source-audit-final.log','tsurugi038-before-after.jpg']
with zipfile.ZipFile(source,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for folder in ['src','scripts','tests','docs','native']:
  for p in sorted((R/folder).rglob('*')):
   if p.is_file() and '__pycache__' not in p.parts and 'bin' not in p.parts and not p.name.startswith('WORK-IN-PROGRESS'):z.write(p,p.relative_to(R))
 for name in ['package.json','package-lock.json','tsconfig.json','README.md']:z.write(R/name,name)
 for name in evidence:z.write(T/name,'validation/'+name)
 z.writestr('SOURCE-SETUP.md','Run npm ci; copy resources/characters from the matching portable package to characters/, and resources/native/wheel-forwarder.exe to native/bin/wheel-forwarder.exe. Run npm run build. Game downloads and Unity caches are excluded. Scope and rendering limits: docs/AUDIT-038.md and docs/HISTORY-RECHECK-038.md.\n')
with zipfile.ZipFile(source) as z:assert z.testzip() is None
report={k:{'path':str(p),'bytes':p.stat().st_size,'sha256':sha(p)} for k,p in [('portable',out),('source',source)]}
(T/'release038.json').write_text(json.dumps(report,indent=2),'utf8');print(json.dumps(report,indent=2))
