import hashlib,json,zipfile,shutil
from pathlib import Path,PurePosixPath
R=Path(__file__).resolve().parents[1];root=R/'release/v0.2.3/win-unpacked';archive=R/'release/BA-Desktop-Pet-0.2.3-win-x64.zip'
def read(name):return json.loads((R/name).read_text('utf8'))
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
validation=read('test-results/wave12-validation.json');assert validation['complete'];package=read('test-results/wave12-package.json');assert package['appAsarSha256']==sha(root/'resources/app.asar')
for item in read('package.json')['build']['extraFiles']:assert (R/item['from']).read_bytes()==(root/item['to']).read_bytes()
files={p.relative_to(root).as_posix():p for p in root.rglob('*') if p.is_file()}
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for name,p in files.items():z.write(p,name)
with zipfile.ZipFile(archive) as z:
 assert z.testzip() is None;names=[i.filename for i in z.infolist() if not i.is_dir()];assert len(names)==len(set(names)) and set(names)==files.keys()
 for name in names:
  assert not PurePosixPath(name).is_absolute() and '..' not in PurePosixPath(name).parts
  with z.open(name) as f:assert hashlib.file_digest(f,'sha256').hexdigest()==sha(files[name]),name
report={'version':'0.2.3','complete':True,'bytes':archive.stat().st_size,'sha256':sha(archive),'matchedFiles':len(files),'zipCrc':True,'addedCharacters':5,'addedCostumes':10,'addedActions':303,'unchangedPreviousResourceFiles':504}
(R/'test-results/release-0.2.3.json').write_text(json.dumps(report,indent=2),'utf8');print(json.dumps(report,indent=2))
