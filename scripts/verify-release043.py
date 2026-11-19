"""Lock the runnable folder and verify the exact installed resource increment."""
from pathlib import Path
import json,hashlib
R=Path(__file__).resolve().parents[1];T=R/'test-results';base=R/'release/v0.2.21/win-unpacked'
read=lambda p:json.loads(p.read_text('utf8'))
def sha(p):
 with p.open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
previous=read(T/'release042-resources.json');specs=read(R/'scripts/roster-wave15.json');old={r['path']:r['sha256']for r in previous};inventory=[]
for p in sorted((R/'characters').rglob('*')):
 if not p.is_file():continue
 rel=str(p.relative_to(R/'characters'));digest=sha(p);assert sha(base/'resources/characters'/rel)==digest
 if rel in old:assert old[rel]==digest,rel
 else:assert p.relative_to(R/'characters').parts[0]in specs,rel
 inventory.append(dict(path=rel,sha256=digest))
assert len(list(p for p in(base/'resources/characters').rglob('*')if p.is_file()))==len(inventory)
report=dict(version='0.2.21',resources=len(inventory),newResources=len(inventory)-len(previous),unchangedPreviousFiles=len(previous),addedOutfits=len(specs),appAsarSha256=sha(base/'resources/app.asar'),executableSha256=sha(base/'BA Desktop Pet.exe'),wheelHelperSha256=sha(base/'resources/native/wheel-forwarder.exe'),zipCreated=False)
(T/'release043-resources.json').write_text(json.dumps(inventory,indent=2),'utf8');(T/'release043-verification.json').write_text(json.dumps(report,indent=2),'utf8');print(json.dumps(report,indent=2))
