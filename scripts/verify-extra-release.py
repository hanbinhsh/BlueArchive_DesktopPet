"""Verify the tested 0.1.17 portable build before publishing its archive."""
import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil
import zipfile

ROOT = Path(__file__).resolve().parents[1]
read = lambda p: json.loads(p.read_text(encoding='utf8'))
sha = lambda p: hashlib.file_digest(p.open('rb'), 'sha256').hexdigest()
package = read(ROOT/'package.json')
assert package['version'] == '0.1.17'
folder = ROOT/'release/v0.1.17'
unpacked = folder/'win-unpacked'
executable = unpacked/'BA Desktop Pet.exe'
archive_path = folder/'BA-Desktop-Pet-0.1.17-win-x64.zip'
expected = set(read(ROOT/'scripts/roster-extras.json'))
records = {name:read(ROOT/f'test-results/{name}.json') for name in [
    'roster', 'hold', 'expressions', 'transitions-packaged', 'extra-panel',
    'extra-costume-resources', 'extra-framing', 'assets', 'expression-source',
    'costume-coverage', 'mouth-uv', 'dpi-toki_armor', 'soak-summary', 'extra-pack-source']}
assert records['extra-pack-source']['version'] == '0.1.17'
assert len(records['extra-pack-source']['matchedBuiltFiles']) == 7
assert records['extra-pack-source']['appAsarSha256'] == sha(unpacked/'resources/app.asar')
assert Path(records['roster']['executable']).resolve() == executable.resolve()
assert records['roster']['restart']
assert {r['character'] for r in records['roster']['results']} == expected
for row in records['roster']['results']:
    manifest = read(ROOT/f"characters/{row['character']}/character.json")
    assert set(row['actions']) == {a['id'] for a in manifest['actions']} - {'idle'}
    assert row['drag'] and row['transparentHitTest'] and row['offline']
for name in ['hold','expressions','transitions-packaged','extra-framing','mouth-uv']:
    assert {r['character'] for r in records[name]} == expected, name
for row in records['hold']:
    assert len(row['samples']) == 23
    assert all(s['diagnostics']['error'] is None for s in row['samples'])
    assert row['samples'][-1]['diagnostics']['frames'] > row['samples'][0]['diagnostics']['frames'] + 400
for row in records['transitions-packaged']:
    assert not row['errors']
    for stage in row['stages']:
        assert sum(.01 < f['transition']['incoming'] < .99 and f['transition']['outgoing'] > .01 for f in stage['frames']) >= 2
panel = records['extra-panel']
assert Path(panel['executable']).resolve() == executable.resolve()
assert panel['thumbnails'] == 65 and panel['offline'] and not panel['errors']
assert panel['walk'] and panel['randomTest'] and panel['interruptNpcInteraction']
assert {r['character'] for r in panel['results']} == expected
assert all(abs(r['scrollAfter']-r['scrollBefore']) <= 2 and r['note'] and r['actionList'] for r in panel['results'])
assert len(records['assets']) == len(records['expression-source']) == 65
coverage = records['costume-coverage']
assert coverage['installedPackCount'] == 65 and not coverage['missing'] and not coverage['unmappedInstalled']
for row in records['extra-costume-resources']['added']:
    assert row['modelSha256'] == sha(ROOT/f"characters/{row['id']}/model.glb")
assert len(records['extra-costume-resources']['unchangedPreviousFiles']) == 238
assert {r['factor'] for r in records['dpi-toki_armor']} == {1,1.5,2}
assert all(Path(r['executable']).resolve()==executable.resolve() and r['diagnostics']['error'] is None for r in records['dpi-toki_armor'])
soak = records['soak-summary']
assert Path(soak['executablePath']).resolve() == executable.resolve()
assert soak['character'] == 'toki_armor' and soak['offlineReload']
assert soak['minutes'] == 30 and soak['elapsedSeconds'] >= 1800 and soak['samples'] >= 179
assert 20 < soak['fps'] <= 32 and not soak['rendererErrors']
assert soak['memoryMiB']['final']-soak['memoryMiB']['first'] < 100
# Check sampling continuity as well as elapsed wall time, so suspend is not a pass.
samples = [json.loads(line) for line in (ROOT/'test-results/soak-samples.jsonl').read_text().splitlines()]
assert len(samples) == soak['samples']
assert all(0 < b['elapsedSeconds']-a['elapsedSeconds'] < 20 for a,b in zip(samples,samples[1:]))
assert all(b['diagnostics']['frames'] > a['diagnostics']['frames'] + 150 for a,b in zip(samples,samples[1:]))
for source in (ROOT/'characters').rglob('*'):
    if source.is_file():
        assert sha(source) == sha(unpacked/'resources/characters'/source.relative_to(ROOT/'characters')), source
for entry in package['build']['extraFiles']:
    assert (ROOT/entry['from']).read_bytes() == (unpacked/entry['to']).read_bytes(), entry
expected_files = {p.relative_to(unpacked).as_posix() for p in unpacked.rglob('*') if p.is_file()}
with zipfile.ZipFile(archive_path) as archive:
    assert archive.testzip() is None
    names = [e.filename for e in archive.infolist() if not e.is_dir()]
    assert len(names) == len(set(names)) and set(names) == expected_files
    for name in names:
        relative = PurePosixPath(name)
        assert not relative.is_absolute() and '..' not in relative.parts
        assert hashlib.sha256(archive.read(name)).hexdigest() == sha(unpacked/name), name
report = {'version':'0.1.17','bytes':archive_path.stat().st_size,'sha256':sha(archive_path),
          'exeSha256':sha(executable),'appAsarSha256':sha(unpacked/'resources/app.asar'),
          'zipCrc':True,'matchedFiles':len(expected_files),'characterResourcesMatch':True,
          'soak30Minutes':True,'results':records,
          'limitations':['Synthetic pointer tests do not verify native system click-through.',
                         'DPI was forced in separate app launches; physical monitor hotplug was not repeated.',
                         'Old furniture resources are unchanged; this run covers the eight added appearance packs.']}
(ROOT/'test-results/release-0.1.17.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
destination = ROOT/'release'/archive_path.name
shutil.copy2(archive_path,destination)
assert sha(destination) == report['sha256']
print(json.dumps({k:v for k,v in report.items() if k not in ['results']},ensure_ascii=False,indent=2))
