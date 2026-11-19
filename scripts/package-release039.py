"""Deliver the exact final executable, including all 0.2.17 repairs and new roles."""
from pathlib import Path
import sys
if '--zip' not in sys.argv:
 raise SystemExit('默认不创建压缩包。仅在用户明确要求时使用 --zip；目录交付请运行 finalize-folder039.py。')
import json,hashlib,zipfile
R=Path(__file__).resolve().parents[1];T=R/'test-results';base=R/'release/v0.2.18/win-unpacked'
def read(n):return json.loads((T/n).read_text('utf8'))
def sha(p):
 with p.open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
s=read('release039-soak.json');assert s['complete']and s['version']=='0.2.18'and s['elapsedSeconds']>=1800 and not s['errors']
v=read('release039-verification.json');assert read('release039-soak-input.json')==v and v['resources']==616
assert sha(base/'resources/app.asar')==v['appAsarSha256']and sha(base/'BA Desktop Pet.exe')==v['executableSha256']
for item in read('release039-resources.json'):
 assert sha(base/'resources/characters'/item['path'])==sha(R/'characters'/item['path'])==item['sha256']
for item in read('release038-resources.json'):
 assert sha(base/'resources/characters'/item['path'])==item['sha256']
assert len(read('wave13-program-identity.json')['identicalRuntimeFiles'])==15
assert sum(r['actions']for r in read('wave13-resources.json')['added'])==128
rt=read('wave13-packaged-runtime.json');assert rt['complete']and rt['restart']and not rt['errors']and len(rt['results'])==4
assert sum(len(r['played'])for r in rt['results'])==124
f=read('faces039-runtime.json');assert f['complete']and len(f['results'])==4 and not f['errors']
assert len(read('final039-runtime.json'))==5 and all(not r['diagnostics']['error']for r in read('final039-runtime.json'))
assert len(read('hold039.json'))==4 and len(read('transitions039.json'))==4 and all(not r['errors']for r in read('transitions039.json'))
assert not read('wave13-persistent-audit.json')['unexplained']
assert all(not r['omitted']for r in read('wave13-fx-adaptation.json'))
surface=read('static039-source-audit.json');assert not surface['errors']and not any(r.get('unadaptedDSFX')or r.get('tintMismatch')for r in surface['rows'])
review=read('visual039-review.json');assert review['newFinalFramesReviewed']==86 and review['newFinalContactSheetsReviewed']==7
assert read('visual038-review.json')['contactSheetsReviewed']==101
assert 'pass 82'in(T/'unit039.log').read_text('utf8')and'Ran 26 tests'in(T/'python039.log').read_text('utf8')
package=json.loads((R/'package.json').read_text('utf8'));assert package['version']=='0.2.18'
for entry in package['build']['extraFiles']:
 p=base/entry['to'];p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((R/entry['from']).read_bytes())
out=R/'release/BA-Desktop-Pet-0.2.18-win-x64.zip';source=R/'release/BA-Desktop-Pet-0.2.18-source.zip'
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED,compresslevel=6)as z:
 for p in sorted(base.rglob('*')):
  if p.is_file():z.write(p,p.relative_to(base))
with zipfile.ZipFile(out)as z:
 assert z.testzip()is None
 for n in z.namelist():
  with z.open(n)as f:assert hashlib.file_digest(f,'sha256').hexdigest()==sha(base/n),n
evidence=['release039-soak.json','release039-soak-input.json','release039-resource-summary.json','release039-verification.json','release039-resources.json','wave13-program-identity.json','wave13-resources.json','wave13-selection.json','wave13-acquisition.json','wave13-partner-acquisition.json','wave13-original-structure.json','wave13-preparation.json','wave13-halos.json','wave13-framing.json','wave13-view-selection.json','wave13-furniture-adaptation.json','wave13-fx-adaptation.json','wave13-persistent-audit.json','wave13-packaged-runtime.json','faces039-runtime.json','final039-runtime.json','hold039.json','transitions039.json','visual039-review.json','unit039.log','python039.log','type039.log','build039.log','assets039.log','static039-source-audit.json','release038-soak.json','release038-resource-summary.json','release038-verification.json','release038-resources.json','resources038-installed.json','stage038-verification.json','visual038-review.json','full038-runtime.json','reported038-runtime.json','boundary038-runtime.json','faces038-runtime.json','release038-speed.json','water038-runtime.json','cloud038-runtime.json','hold038.json','transitions038.json','menu038.json','scroll038.json','tsurugi038-before-after.jpg']
with zipfile.ZipFile(source,'w',zipfile.ZIP_DEFLATED,compresslevel=6)as z:
 for folder in ['src','scripts','tests','docs','native']:
  for p in sorted((R/folder).rglob('*')):
   if p.is_file()and'__pycache__'not in p.parts and'bin'not in p.parts and not p.name.startswith('WORK-IN-PROGRESS'):z.write(p,p.relative_to(R))
 for n in ['package.json','package-lock.json','tsconfig.json','README.md']:z.write(R/n,n)
 for n in evidence+['wave13-reference.json','sandbath039-official-release-reference.jpg']:z.write(T/n,'validation/'+n)
 for prefix in ['final039-contact-','faces039-contact-']:
  for p in sorted(T.glob(prefix+'*.jpg')):z.write(p,'validation/'+p.name)
 z.writestr('SOURCE-SETUP.md','Run npm ci; copy resources/characters from the matching 0.2.18 portable ZIP to characters/, and resources/native/wheel-forwarder.exe to native/bin/wheel-forwarder.exe. Run npm run build. Game downloads and Unity caches are excluded. See docs/ROSTER-013.md and docs/AUDIT-038.md for sources, validation and scope.\n')
with zipfile.ZipFile(source)as z:assert z.testzip()is None
report={k:{'path':str(p),'bytes':p.stat().st_size,'sha256':sha(p)}for k,p in [('portable',out),('source',source)]}
(T/'release039.json').write_text(json.dumps(report,indent=2),'utf8');print(json.dumps(report,indent=2))
