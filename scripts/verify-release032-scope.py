"""Check all packaged character bytes and precisely describe the release delta."""
from pathlib import Path
import hashlib
import json

root = Path(__file__).resolve().parent.parent
source = root / 'characters'
packed = root / 'release/v0.2.12/win-unpacked/resources/characters'
previous = root / 'release/v0.2.11/win-unpacked/resources/characters'

def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

def inventory(path):
    return {p.relative_to(path).as_posix(): digest(p)
            for p in sorted(path.rglob('*')) if p.is_file()}

installed = inventory(source)
assert installed and installed == inventory(packed), 'Packaged character resources differ'
old = inventory(previous)
assert installed.keys() == old.keys(), 'Unexpected character resource additions/removals'
changed = [name for name in installed if installed[name] != old[name]]
assert all(name.endswith('.glb') and not name.endswith('/model.glb') for name in changed)
adaptation = json.loads((root / 'test-results/full032-final-adaptation.json').read_text('utf8'))
report = {
    'complete': True, 'version': '0.2.12',
    'packagedCharacterFiles': len(installed), 'changedFurnitureModels': changed,
    'ordinaryModelsAndManifestsUnchanged': True,
    'adaptedEntries': len(adaptation),
    'entriesWithoutOmissions': sum(not r['omitted'] for r in adaptation),
    'particleInstances': sum(r['particles'] for r in adaptation),
    'unresolvedSourceBindings': [r for r in adaptation if r['omitted']],
    'sha256': installed,
}
(root / 'test-results/release032-scope.json').write_text(json.dumps(report, indent=2, ensure_ascii=False), 'utf8')
print(json.dumps({k:v for k,v in report.items() if k not in ('sha256', 'changedFurnitureModels', 'unresolvedSourceBindings')}, indent=2))
print('Changed furniture GLBs:', len(changed))
