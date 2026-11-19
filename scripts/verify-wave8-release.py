"""Publish the archive only after packaged tests and file parity checks."""
import hashlib,json,shutil,sys,zipfile
from pathlib import Path,PurePosixPath
R=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
p=read(R/'package.json');assert p['version']=='0.1.19'
folder=R/'release/v0.1.19';unpacked=folder/'win-unpacked';exe=unpacked/'BA Desktop Pet.exe'
records={name:read(R/f'test-results/{name}.json') for name in ['expanded-runtime','wave8-panel','wave8-hold','wave8-transitions','wave8-expressions','expanded-resources','costume-coverage','wiki-model-comparison','wave8-pack-source','wave8-runtime-suite']}
manifests={f.parent.name:read(f) for f in (R/'characters').glob('*/character.json')}
new=set(read(R/'.assets/wave8-all-specs.json'))
assert len(manifests)==100 and sum(len(c['actions']) for c in manifests.values())==2487
runtime=records['expanded-runtime']
assert runtime['complete'] and runtime['restart'] and not runtime['errors']
assert Path(runtime['executable']).resolve()==exe.resolve()
assert Path(runtime['root']).resolve()==(unpacked/'resources/characters').resolve()
assert {r['character'] for r in runtime['results']}==set(manifests)
for r in runtime['results']:
    assert r['offline'] and r['returnedToIdle'] and r['available']==len(manifests[r['character']]['actions'])
    if r['character'] in new:assert set(r['played'])=={a['id'] for a in manifests[r['character']]['actions'] if a['id']!='idle'}
panel=records['wave8-panel'];assert panel['offline'] and not panel['errors'] and panel['thumbnails']==100
assert Path(panel['executable']).resolve()==exe.resolve()
assert {r['character'] for r in panel['results']}==new
assert all(abs(r['scrollAfter']-r['scrollBefore'])<=2 and r['note'] and r['actionList'] for r in panel['results'])
for name in ['wave8-hold','wave8-transitions','wave8-expressions']:
    assert {r['character'] for r in records[name]}==new,name
for r in records['wave8-hold']:
    assert len(r['samples'])==23
    assert all(s['diagnostics']['error'] is None for s in r['samples'])
    assert r['samples'][-1]['diagnostics']['frames']>r['samples'][0]['diagnostics']['frames']+200
for r in records['wave8-transitions']:
    assert not r['errors']
    assert all(sum(.01<f['transition']['incoming']<.99 and f['transition']['outgoing']>.01 for f in s['frames'])>=2 for s in r['stages'])
assert len(records['wave8-runtime-suite'])==4 and all(r['exitCode']==0 for r in records['wave8-runtime-suite'])
resource=records['expanded-resources'];assert len(resource)==100
assert sum(r.get('unchangedCommonAnimations',0) for r in resource)==459
assert sum(r.get('unchangedFurniture',0) for r in resource)==79
for r in resource:assert sha(R/'characters'/r['character']/'model.glb')==r['modelSha256']
coverage=records['costume-coverage'];assert coverage['installedPackCount']==100 and not coverage['missing'] and not coverage['unmappedInstalled']
assert len(records['wiki-model-comparison'])==99
source=records['wave8-pack-source'];assert source['appAsarSha256']==sha(unpacked/'resources/app.asar')
assert source['version']=='0.1.19' and len(source['matchedBuiltFiles'])==7
expected={f.relative_to(R/'characters') for f in (R/'characters').rglob('*') if f.is_file()}
actual={f.relative_to(unpacked/'resources/characters') for f in (unpacked/'resources/characters').rglob('*') if f.is_file()}
assert actual==expected
for f in expected:assert sha(R/'characters'/f)==sha(unpacked/'resources/characters'/f),f
for item in p['build']['extraFiles']:assert (R/item['from']).read_bytes()==(unpacked/item['to']).read_bytes(),item
if '--preflight' in sys.argv:
    print('Runtime, source, resources and documentation parity passed');sys.exit(0)
archive_path=folder/'BA-Desktop-Pet-0.1.19-win-x64.zip'
files={f.relative_to(unpacked).as_posix() for f in unpacked.rglob('*') if f.is_file()}
with zipfile.ZipFile(archive_path) as archive:
    assert archive.testzip() is None
    entries=[e.filename for e in archive.infolist() if not e.is_dir()]
    assert len(entries)==len(set(entries)) and set(entries)==files
    for name in entries:
        relative=PurePosixPath(name);assert not relative.is_absolute() and '..' not in relative.parts
        with archive.open(name) as f:assert hashlib.file_digest(f,'sha256').hexdigest()==sha(unpacked/name),name
report={'version':'0.1.19','bytes':archive_path.stat().st_size,'sha256':sha(archive_path),'matchedFiles':len(files),'zipCrc':True,'newSoak30Minutes':False,'results':records,
        'limitations':['Synthetic input tests do not replace native OS click-through or physical monitor hotplug.',
        'No fresh 30-minute soak or physical DPI tests in this release.',
        'All new actions are smoke-tested; common interaction natural completion is checked separately. Old packs use category sampling.',
        'Unity particles, audio, attack targets and scene-dependent models are not reproduced. See MODEL-AUDIT.md.']}
(R/'test-results/release-0.1.19.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
destination=R/'release'/archive_path.name;shutil.copy2(archive_path,destination);assert sha(destination)==report['sha256']
print(json.dumps({k:v for k,v in report.items() if k!='results'},ensure_ascii=False,indent=2))
