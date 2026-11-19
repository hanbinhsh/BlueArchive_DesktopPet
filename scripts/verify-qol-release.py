import hashlib,json,shutil,zipfile
from pathlib import Path,PurePosixPath
R=Path(__file__).resolve().parents[1]
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def files(root):return {p.relative_to(root).as_posix():p for p in root.rglob('*') if p.is_file()}
folder=R/'release/v0.2.0-final';unpacked=folder/'win-unpacked'
package=json.loads((R/'test-results/qol-release-package.json').read_text())
assert package['complete'] and package['appAsarSha256']==sha(unpacked/'resources/app.asar')
assert package['changedSinceSoak']==['main.cjs']
expected=files(unpacked)
for entry in json.loads((R/'package.json').read_text())['build']['extraFiles']:
    assert (R/entry['from']).read_bytes()==(unpacked/entry['to']).read_bytes()
baseline=files(R/'release/v0.1.22/win-unpacked/resources/characters');current=files(R/'characters')
assert not baseline.keys()-current.keys()
changed=[n for n in baseline if sha(baseline[n])!=sha(current[n])];added=sorted(current.keys()-baseline.keys())
assert sorted(changed)==['hina_pajamas/character.json','kisaki/character.json'],changed
assert len(added)==3 and all(n.endswith('.glb') for n in added),added
archive=folder/'BA-Desktop-Pet-0.2.0-win-x64.zip'
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
    names=[e.filename for e in z.infolist() if not e.is_dir()]
    assert len(names)==len(set(names)) and set(names)==expected.keys()
    for n in names:
        assert not PurePosixPath(n).is_absolute() and '..' not in PurePosixPath(n).parts
        with z.open(n) as f:assert hashlib.file_digest(f,'sha256').hexdigest()==sha(expected[n]),n
report={'version':'0.2.0','complete':True,'bytes':archive.stat().st_size,'sha256':sha(archive),'matchedFiles':len(expected),'zipCrc':True,'resourceChanges':changed,'resourcesAdded':added,'soak':'qol-release-soak.json','soakScope':'Final renderer/assets; main-process startup readback and development-profile isolation corrected afterward and separately retested.'}
(R/'test-results/release-0.2.0.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
dest=R/'release'/archive.name;shutil.copy2(archive,dest);assert sha(dest)==report['sha256']
print(json.dumps(report,ensure_ascii=False,indent=2))
