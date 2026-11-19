"""Package only the exact 0.2.15 payload that passed the completed soak."""
from pathlib import Path
import hashlib,json,zipfile
root=Path(__file__).resolve().parent.parent;base=root/'release/v0.2.15/win-unpacked'
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
soak=json.loads((root/'test-results/release036-soak.json').read_text('utf8'))
assert soak['complete'] and soak['version']=='0.2.15' and soak['elapsedSeconds']>=1800 and not soak['errors']
verified=json.loads((root/'test-results/release036-verification.json').read_text('utf8'))
assert sha(base/'resources/app.asar')==verified['appAsarSha256']
assert sha(base/'BA Desktop Pet.exe')==verified['executableSha256']
for item in json.loads((root/'test-results/release036-resources.json').read_text('utf8')):
 assert sha(base/'resources/characters'/item['path'])==item['sha256']
 assert sha(root/'characters'/item['path'])==item['sha256']
rows=json.loads((root/'test-results/packaged036-runtime.json').read_text('utf8'))
assert len(rows)==145 and all(not r['diagnostics'].get('error') for r in rows)
package=json.loads((root/'package.json').read_text('utf8'));assert package['version']=='0.2.15'
for item in package['build']['extraFiles']:
 p=base/item['to'];p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((root/item['from']).read_bytes())
out=root/'release/BA-Desktop-Pet-0.2.15-win-x64.zip';source=root/'release/BA-Desktop-Pet-0.2.15-source.zip'
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for p in sorted(base.rglob('*')):
  if p.is_file():z.write(p,p.relative_to(base))
with zipfile.ZipFile(out) as z:
 assert z.testzip() is None
 for name in z.namelist():
  with z.open(name) as f:assert hashlib.file_digest(f,'sha256').hexdigest()==sha(base/name),name
with zipfile.ZipFile(source,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for folder in ['src','scripts','tests','docs','native']:
  for p in sorted((root/folder).rglob('*')):
   if p.is_file() and '__pycache__' not in p.parts and 'bin' not in p.parts:z.write(p,p.relative_to(root))
 for name in ['package.json','package-lock.json','tsconfig.json','README.md']:z.write(root/name,name)
 for name in ['release036-soak.json','release036-resource-summary.json','packaged036-visual-review.json','bubble036-runtime.json','depth036-source.json','release036-verification.json','release036-resources.json','resources036-installed.json','stage036-verification.json','unit036-final.log','type036-final.log','python036-final.log','unity036-pivot.txt','audit036-runtime.json','packaged036-runtime.json','water036-runtime.json','mesh-pivot036-applied.json']:
  z.write(root/'test-results'/name,'validation/'+name)
 z.write(root/'.assets/unity036/Assets/Editor/ParticleProbe.cs','validation/ParticleProbe.cs')
 z.writestr('SOURCE-SETUP.md','Run npm ci; copy resources/characters from the portable package to characters/, and resources/native/wheel-forwarder.exe to native/bin/wheel-forwarder.exe. Run npm run build. The source ZIP excludes game downloads and Unity caches. See docs/AUDIT-036.md for scope and original rendering limitations.\n')
with zipfile.ZipFile(source) as z:assert z.testzip() is None
report={k:{'path':str(p),'bytes':p.stat().st_size,'sha256':sha(p)} for k,p in [('portable',out),('source',source)]}
(root/'test-results/release036.json').write_text(json.dumps(report,indent=2),'utf8');print(json.dumps(report,indent=2))
