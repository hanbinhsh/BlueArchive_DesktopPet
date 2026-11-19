import hashlib,json,shutil,zipfile
from pathlib import Path,PurePosixPath
R=Path(__file__).resolve().parents[1]
def read(p):return json.loads((R/p).read_text(encoding='utf8'))
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def files(root):return {p.relative_to(root).as_posix():p for p in root.rglob('*') if p.is_file()}
root=R/'release/v0.2.1/win-unpacked';folder=root.parent;spec=read('scripts/roster-wave10.json')
runtime=read('test-results/wave10-packaged-runtime.json');assert runtime['complete'] and not runtime['errors']
assert Path(runtime['executable']).resolve()==(root/'BA Desktop Pet.exe').resolve()
assert {x['character'] for x in runtime['results']}==set(spec)
assert sum(len(x['played']) for x in runtime['results'])==259
assert read('test-results/wave10-library.json')['complete']
assert read('test-results/wave10-packaged-scroll.json')['complete']
for name in ['hold','transitions','expressions']:
 d=read('test-results/wave10-'+name+'.json');assert {x['character'] for x in d}==set(spec),(name,len(d))
package=read('test-results/wave10-package.json');assert package['complete'] and package['appAsarSha256']==sha(root/'resources/app.asar')
assert len(read('test-results/wave10-resources.json')['unchangedPreviousFiles'])==420
for entry in read('package.json')['build']['extraFiles']:assert (R/entry['from']).read_bytes()==(root/entry['to']).read_bytes()
archive=folder/'BA-Desktop-Pet-0.2.1-win-x64.zip';expected=files(root)
with zipfile.ZipFile(archive) as z:
 assert z.testzip() is None
 names=[e.filename for e in z.infolist() if not e.is_dir()];assert len(names)==len(set(names)) and set(names)==expected.keys()
 for n in names:
  assert not PurePosixPath(n).is_absolute() and '..' not in PurePosixPath(n).parts
  with z.open(n) as f:assert hashlib.file_digest(f,'sha256').hexdigest()==sha(expected[n]),n
report={'version':'0.2.1','complete':True,'bytes':archive.stat().st_size,'sha256':sha(archive),'matchedFiles':len(expected),'zipCrc':True,'addedCharacters':5,'addedOutfits':9,'addedActions':268,'unchangedPreviousResourceFiles':420}
(R/'test-results/release-0.2.1.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
dest=R/'release'/archive.name;shutil.copy2(archive,dest);assert sha(dest)==report['sha256'];print(json.dumps(report,ensure_ascii=False,indent=2))
