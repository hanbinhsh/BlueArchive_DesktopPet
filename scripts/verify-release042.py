"""Lock the one-resource release and prove every other resource unchanged."""
from pathlib import Path
import json,hashlib
R=Path(__file__).resolve().parents[1];T=R/'test-results';base=R/'release/v0.2.20/win-unpacked'
read=lambda p:json.loads(p.read_text('utf8'))
def sha(p):
 with p.open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
old=read(T/'release040-resources.json');proof=read(T/'ichika042-resource-proof.json');changed=[];inventory=[]
for row in old:
 rel=row['path'];a=sha(R/'characters'/rel);b=sha(base/'resources/characters'/rel);assert a==b,rel
 if a!=row['sha256']:changed.append(rel);assert a==proof['afterSha256']and row['sha256']==proof['beforeSha256']
 inventory.append(dict(path=rel,sha256=a))
assert list(map(lambda s:s.replace('\\','/'),changed))==['ichika/f10206_0.glb']
assert len(list(p for p in(base/'resources/characters').rglob('*')if p.is_file()))==len(inventory)==676
report=dict(version='0.2.20',resources=676,unchangedPreviousFiles=675,changedResources=changed,appAsarSha256=sha(base/'resources/app.asar'),executableSha256=sha(base/'BA Desktop Pet.exe'),wheelHelperSha256=sha(base/'resources/native/wheel-forwarder.exe'))
(T/'release042-resources.json').write_text(json.dumps(inventory,indent=2),'utf8');(T/'release042-verification.json').write_text(json.dumps(report,indent=2),'utf8');print(json.dumps(report,indent=2))
