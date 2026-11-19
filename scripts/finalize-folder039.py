"""Validate and deliver the tested 0.2.18 folder without creating archives."""
from pathlib import Path
import json,hashlib
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

import shutil
evidence=['release039-resource-summary.json','release039-verification.json','release039-resources.json','wave13-program-identity.json','wave13-resources.json','wave13-selection.json','wave13-acquisition.json','wave13-original-structure.json','wave13-framing.json','wave13-reference.json','visual039-review.json','wave13-persistent-audit.json','release038-resources.json','visual038-review.json','tsurugi038-before-after.jpg','sandbath039-official-release-reference.jpg']
validation=base/'validation';validation.mkdir(exist_ok=True)
for name in evidence:shutil.copy2(T/name,validation/name)
for prefix in ['final039-contact-','faces039-contact-']:
 for p in T.glob(prefix+'*.jpg'):shutil.copy2(p,validation/p.name)
docs=base/'docs';docs.mkdir(exist_ok=True)
for p in (R/'docs').glob('*.md'):
 if not p.name.startswith('WORK-IN-PROGRESS'):shutil.copy2(p,docs/p.name)
readme=base/'使用说明.md'
readme.write_text(readme.read_text('utf8').replace('`release/v0.2.18/win-unpacked/BA Desktop Pet.exe`','`BA Desktop Pet.exe`'),'utf8')
summary={'version':'0.2.18','zipCreated':False,'soak':{k:s[k] for k in ['complete','elapsedSeconds','fps','cycles','selections','errors','memoryMiB']},'outfits':154,'actions':3936,'furniture':150,'newOutfits':4,'newActions':128,'newFurniture':5,'historicalFramesReviewed':1468,'newFramesReviewed':86,'runtimeFilesUnchanged':15,'oldResourcesUnchanged':599,'sourceDirectory':str(R),'fullTestRecords':str(T),'packagingPreference':'Directory by default; ZIP only on explicit request.'}
(validation/'summary039.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),'utf8')
files=[{'path':str(p.relative_to(base)),'bytes':p.stat().st_size,'sha256':sha(p)}for p in sorted(base.rglob('*'))if p.is_file()]
report={'version':'0.2.18','directory':str(base),'executable':str(base/'BA Desktop Pet.exe'),'zipCreated':False,'bytes':sum(f['bytes']for f in files),'files':files}
(T/'release039-folder.json').write_text(json.dumps(report,indent=2),'utf8')
print(json.dumps({k:v for k,v in report.items() if k!='files'},indent=2))
