"""Deliver the verified 0.2.19 folder; never create an archive."""
from pathlib import Path
import json,hashlib,shutil
R=Path(__file__).resolve().parents[1];T=R/'test-results';base=R/'release/v0.2.19/win-unpacked'
read=lambda n:json.loads((T/n).read_text('utf8'))
def sha(p):
 with p.open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
s=read('release040-soak.json');assert s['complete']and s['version']=='0.2.19'and s['elapsedSeconds']>=1800 and not s['errors']
v=read('release040-verification.json');assert read('release040-soak-input.json')==v and v['resources']==676
assert sha(base/'resources/app.asar')==v['appAsarSha256']and sha(base/'BA Desktop Pet.exe')==v['executableSha256']
for item in read('release040-resources.json'):assert sha(base/'resources/characters'/item['path'])==sha(R/'characters'/item['path'])==item['sha256']
for item in read('release039-resources.json'):assert sha(base/'resources/characters'/item['path'])==item['sha256']
program=read('wave14-program-identity.json');assert len(program['identicalRuntimeFiles'])==14 and program['changedRuntimeFiles']==['/dist/renderer.js']
resources=read('wave14-resources.json');assert sum(r['actions']for r in resources['added'])==369 and resources['unchangedPreviousFiles']==616
rt=read('wave14-packaged-runtime.json');assert rt['complete']and rt['restart']and not rt['errors']and len(rt['results'])==15 and sum(len(r['played'])for r in rt['results'])==354
f=read('faces040-runtime.json');assert f['complete']and len(f['results'])==15 and not f['errors']and sum(len(x['samples'])for x in f['results'])==132
assert len(read('final040-runtime.json'))==15 and all(not r['diagnostics']['error']for r in read('final040-runtime.json'))
assert len(read('hold040.json'))==5 and len(read('transitions040.json'))==5 and all(not r['errors']for r in read('transitions040.json'))
assert not read('wave14-persistent-audit.json')['unexplained']and all(not r['omitted']for r in read('wave14-fx-adaptation.json'))
surface=read('static040-source-audit.json');assert not surface['errors']and not any(r.get('unadaptedDSFX')or r.get('tintMismatch')for r in surface['rows'])
review=read('visual040-review.json');assert review['newFinalFramesReviewed']==282 and review['newFinalContactSheetsReviewed']==30
assert 'pass 82'in(T/'release040-core-tests.log').read_text('utf8')and'Ran 29 tests'in(T/'release040-python-tests.log').read_text('utf8')
c=read('wave14-census.json');assert c['installedPlayable']==78 and c['remainingPlayable']==71 and c['playableTotal']==149 and c['outfits']==169 and c['actions']==4305 and c['furniture']==165
package=json.loads((R/'package.json').read_text('utf8'));assert package['version']=='0.2.19'
for entry in package['build']['extraFiles']:
 p=base/entry['to'];p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(R/entry['from'],p)
validation=base/'validation';validation.mkdir(exist_ok=True)
evidence=['release040-verification.json','release040-resources.json','wave14-program-identity.json','wave14-resources.json','wave14-selection.json','wave14-census.json','wave14-acquisition.json','wave14-original-structure.json','wave14-framing.json','wave14-view-selection.json','visual040-review.json','wave14-persistent-audit.json','wave14-fx-adaptation.json','static040-source-audit.json','wave14-packaged-runtime.json','faces040-runtime.json','final040-runtime.json','hold040.json','transitions040.json','release040-soak.json','release040-soak-input.json','release040-soak-cases.json','release039-resources.json','visual039-review.json','visual038-review.json','wave14-furniture-adaptation.json','wave14-fx-dependencies.json','shimiko14-book-dependency.json','tomoe14-null-renderers.json']
for name in evidence:shutil.copy2(T/name,validation/name)
for prefix in ['final040-contact-','faces040-contact-']:
 for p in T.glob(prefix+'*.jpg'):shutil.copy2(p,validation/p.name)
docs=base/'docs';docs.mkdir(exist_ok=True)
for p in(R/'docs').glob('*.md'):
 if not p.name.startswith('WORK-IN-PROGRESS'):shutil.copy2(p,docs/p.name)
p=base/'使用说明.md';p.write_text(p.read_text('utf8').replace('`release/v0.2.19/win-unpacked/BA Desktop Pet.exe`','`BA Desktop Pet.exe`'),'utf8')
summary=dict(version='0.2.19',zipCreated=False,sourceDirectory=str(R),fullTestRecords=str(T),outfits=169,actions=4305,furniture=165,newPlayableStudents=10,newOutfits=15,newActions=369,newFurniture=15,installedPlayable=78,totalPlayable=149,remainingPlayable=71,extraNpc='Plana',newFramesReviewed=282,newContactSheets=30,oldResourcesUnchanged=616,unchangedRuntimeFiles=14,changedRuntimeFiles=program['changedRuntimeFiles'],soak={k:s[k]for k in ['complete','elapsedSeconds','fps','cycles','selections','errors','memoryMiB']})
(validation/'summary040.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),'utf8')
files=[dict(path=str(p.relative_to(base)),bytes=p.stat().st_size,sha256=sha(p))for p in sorted(base.rglob('*'))if p.is_file()]
report=dict(version='0.2.19',directory=str(base),executable=str(base/'BA Desktop Pet.exe'),zipCreated=False,bytes=sum(f['bytes']for f in files),files=files)
(T/'release040-folder.json').write_text(json.dumps(report,indent=2),'utf8');print(json.dumps({k:v for k,v in report.items()if k!='files'},indent=2))
