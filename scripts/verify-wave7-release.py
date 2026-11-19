"""Publish only the archive whose resources and runtime were actually checked."""
import hashlib,json,shutil,zipfile,sys
from pathlib import Path,PurePosixPath
R=Path(__file__).resolve().parents[1]
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
package=read(R/'package.json');assert package['version']=='0.1.18'
folder=R/'release/v0.1.18';unpacked=folder/'win-unpacked';exe=unpacked/'BA Desktop Pet.exe'
archive_path=folder/'BA-Desktop-Pet-0.1.18-win-x64.zip'
expected=set(read(R/'scripts/roster-wave7.json'))
names=['roster','hold','expressions','transitions-packaged','wave7-panel','wave7-resources',
       'wave7-framing','assets','expression-source','costume-coverage','mouth-uv','wave7-halos',
       'furniture-runtime','furniture-runtime-run','furniture-assets','furniture-coverage',
       'wave7-runtime-delta','wave7-pack-source','wave7-runtime-suite',
       'wave7-hifumi-first-hold-trace','wave7-kokona-first-hold-trace','wave7-miyu_swimsuit-first-hold-trace',
       'wave7-kurumi-first-hold-trace','wave7-before-size-fix','wave7-size-runtime','wave7-size-framing']
records={name:read(R/f'test-results/{name}.json') for name in names}
assert all(r['exitCode']==0 for r in records['wave7-runtime-suite'])
assert len(records['wave7-runtime-suite'])==6
assert records['wave7-pack-source']['appAsarSha256']==sha(unpacked/'resources/app.asar')
assert records['wave7-pack-source']['version']=='0.1.18'
assert len(records['wave7-pack-source']['matchedBuiltFiles'])==7
assert len(records['wave7-runtime-delta'])==7
assert {r['name'] for r in records['wave7-runtime-delta'] if not r['unchanged']}=={'main.cjs','renderer.js'}
baseline=records['wave7-before-size-fix']
assert {r['character'] for r in baseline['roster']['results']}==expected
assert baseline['roster']['restart']
for name in ['hold','expressions','transitions-packaged']:
    assert {r['character'] for r in baseline[name]}==expected
assert len(baseline['wave7-runtime-suite'])==4 and all(r['exitCode']==0 for r in baseline['wave7-runtime-suite'])
focused={'hifumi','izuna'}
assert Path(records['roster']['executable']).resolve()==exe.resolve() and records['roster']['restart']
assert {r['character'] for r in records['roster']['results']}==focused
for r in records['roster']['results']:
    c=read(R/f"characters/{r['character']}/character.json")
    assert set(r['actions'])=={a['id'] for a in c['actions']}-{'idle'}
    assert r['offline'] and r['drag'] and r['transparentHitTest']
for name in ['wave7-framing','mouth-uv']:
    assert {r['character'] for r in records[name]}==expected,name
for name in ['hold','expressions','transitions-packaged','wave7-size-framing']:
    assert {r['character'] for r in records[name]}==focused,name
assert {r['character'] for r in records['wave7-size-runtime']['results']}==focused
assert Path(records['wave7-size-runtime']['executable']).resolve()==exe.resolve()
for r in records['wave7-size-runtime']['results']:
    assert r['idle']['max'][1]-r['idle']['min'][1]>1.25
    assert r['restored']['zoom']==1 and r['restored']['centerY']==1
for r in records['hold']+baseline['hold']:
    assert len(r['samples'])==23
    assert all(s['diagnostics']['error'] is None and s['diagnostics']['action']=='pickup' for s in r['samples'])
    assert r['samples'][-1]['diagnostics']['frames']>r['samples'][0]['diagnostics']['frames']+400
for r in records['transitions-packaged']+baseline['transitions-packaged']:
    assert not r['errors']
    assert len(r['stages'])>=3
    for stage in r['stages']:
        assert sum(.01<f['transition']['incoming']<.99 and f['transition']['outgoing']>.01 for f in stage['frames'])>=2
panel=records['wave7-panel']
assert Path(panel['executable']).resolve()==exe.resolve() and panel['offline'] and not panel['errors']
assert panel['thumbnails']==84 and {r['character'] for r in panel['results']}==expected
assert all(abs(r['scrollAfter']-r['scrollBefore'])<=2 and r['note'] and r['actionList'] for r in panel['results'])
assert len(records['assets'])==len(records['expression-source'])==84
assert set(records['wave7-halos'])==expected
coverage=records['costume-coverage']
assert coverage['installedPackCount']==84 and not coverage['missing'] and not coverage['unmappedInstalled']
for r in records['wave7-resources']['added']:assert r['modelSha256']==sha(R/f"characters/{r['id']}/model.glb")
assert len(records['wave7-resources']['unchangedPreviousFiles'])==262
furn={(key,f['id']) for key in expected for f in read(R/f'characters/{key}/character.json').get('furniture',[])}
assert len(furn)==13 and {(r['character'],r['furniture']) for r in records['furniture-runtime']}==furn
assert records['furniture-runtime-run']['complete'] and records['furniture-runtime-run']['offline']
assert Path(records['furniture-runtime-run']['executable']).resolve()==exe.resolve()
assert len(records['furniture-assets'])==records['furniture-coverage']['interactions']==79
assert not records['furniture-coverage']['unadaptedMappedInteractions']
for p in (R/'characters').rglob('*'):
    if p.is_file():assert sha(p)==sha(unpacked/'resources/characters'/p.relative_to(R/'characters')),p
for item in package['build']['extraFiles']:assert (R/item['from']).read_bytes()==(unpacked/item['to']).read_bytes(),item
if '--preflight' in sys.argv:
    print('Runtime, source, resource and documentation parity checks passed')
    sys.exit(0)
files={p.relative_to(unpacked).as_posix() for p in unpacked.rglob('*') if p.is_file()}
with zipfile.ZipFile(archive_path) as archive:
    assert archive.testzip() is None
    entries=[e.filename for e in archive.infolist() if not e.is_dir()]
    assert len(entries)==len(set(entries)) and set(entries)==files
    for name in entries:
        relative=PurePosixPath(name);assert not relative.is_absolute() and '..' not in relative.parts
        assert hashlib.sha256(archive.read(name)).hexdigest()==sha(unpacked/name),name
report={'version':'0.1.18','bytes':archive_path.stat().st_size,'sha256':sha(archive_path),
        'exeSha256':sha(exe),'appAsarSha256':sha(unpacked/'resources/app.asar'),
        'matchedFiles':len(files),'zipCrc':True,'characterResourcesMatch':True,
        'newSoak30Minutes':False,'priorSoakEvidence':'release-0.1.17.json',
        'results':records,'limitations':['This release tests 19 added appearances and 13 new furniture interactions.',
        'Initial Hifumi, Kokona, swimsuit Miyu and Kurumi sustained-hold tests recorded lostpointercapture and returned to idle. Their causes are unknown; repeated tests are reported separately.',
        '262 previous resource files are unchanged. Runtime changes add optional framing and camera interpolation for Hifumi and Izuna.',
        'The initial 19-pack checks preceded the size correction; final focused checks cover those two changed packs, all 13 new furniture interactions and the 84-card panel.',
        'Synthetic pointer tests do not replace native OS click-through tests.',
        'Physical monitor hotplug, new DPI runs and a new 30-minute soak were not repeated.',
        'Unity-specific particles, audio, refraction and water-wave shaders are not reproduced.']}
(R/'test-results/release-0.1.18.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
destination=R/'release'/archive_path.name;shutil.copy2(archive_path,destination);assert sha(destination)==report['sha256']
print(json.dumps({k:v for k,v in report.items() if k!='results'},ensure_ascii=False,indent=2))
