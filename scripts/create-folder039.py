"""Reuse release validation gates to create a directory-only finalizer."""
from pathlib import Path
S=Path(__file__).resolve().parent
text=(S/'package-release039.py').read_text('utf8')
checks=text[text.index("R=Path(__file__)"):text.index("out=R/'release/")]
tail='''
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
'''
(S/'finalize-folder039.py').write_text('"""Validate and deliver the tested 0.2.18 folder without creating archives."""\nfrom pathlib import Path\nimport json,hashlib\n'+checks+tail,'utf8')
