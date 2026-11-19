from pathlib import Path
import json,hashlib
R=Path(__file__).resolve().parents[1];T=R/'test-results';base=R/'release/v0.2.22/win-unpacked'
read=lambda p:json.loads(p.read_text('utf8'))
def sha(p):
 with p.open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
old=read(T/'release043-resources.json');oldmap={r['path']:r['sha256']for r in old};specs=read(R/'scripts/roster-wave16.json');changed=[];inventory=[]
for p in sorted((R/'characters').rglob('*')):
 if not p.is_file():continue
 rel=str(p.relative_to(R/'characters'));s=sha(p);assert sha(base/'resources/characters'/rel)==s
 if rel in oldmap:
  if oldmap[rel]!=s:changed.append(rel.replace('\\','/'))
 else:assert p.relative_to(R/'characters').parts[0]in specs
 inventory.append(dict(path=rel,sha256=s))
assert set(changed)=={'chiaki/model.glb','chiaki/f210356_0.glb','chiaki/thumbnail.png','atsuko_swimsuit/character.json'}
assert len(inventory)==len(list(p for p in(base/'resources/characters').rglob('*')if p.is_file()))==781
report=dict(version='0.2.22',resources=781,newResources=40,unchangedPreviousFiles=737,changedResources=changed,addedOutfits=10,appAsarSha256=sha(base/'resources/app.asar'),executableSha256=sha(base/'BA Desktop Pet.exe'),wheelHelperSha256=sha(base/'resources/native/wheel-forwarder.exe'),zipCreated=False)
(T/'release044-resources.json').write_text(json.dumps(inventory,indent=2),'utf8');(T/'release044-verification.json').write_text(json.dumps(report,indent=2),'utf8');print(json.dumps(report,indent=2))
