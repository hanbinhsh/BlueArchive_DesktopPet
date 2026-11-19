"""Record the exact executable payload and every offline resource under test."""
from pathlib import Path
import hashlib,json
root=Path(__file__).resolve().parent.parent;base=root/'release/v0.2.16/win-unpacked'
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
inventory=[]
for p in sorted((root/'characters').rglob('*')):
 if p.is_file():
  rel=p.relative_to(root/'characters');target=base/'resources/characters'/rel
  assert target.exists() and sha(p)==sha(target),rel
  inventory.append({'path':str(rel),'sha256':sha(p)})
package=json.loads((root/'package.json').read_text('utf8'));assert package['version']=='0.2.16'
report={'version':'0.2.16','appAsarSha256':sha(base/'resources/app.asar'),'executableSha256':sha(base/'BA Desktop Pet.exe'),'resources':len(inventory)}
(root/'test-results/release037-resources.json').write_text(json.dumps(inventory,indent=2),'utf8')
(root/'test-results/release037-verification.json').write_text(json.dumps(report,indent=2),'utf8');print(report)
