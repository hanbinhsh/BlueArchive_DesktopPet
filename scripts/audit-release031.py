"""Check the patch changes only renderer metadata in the 22 intended models."""
from pathlib import Path
import hashlib
import json
from glb import load

root = Path(__file__).resolve().parent.parent
current = root / 'characters'
packaged = root / 'release/v0.2.11/win-unpacked/resources/characters'
previous = root / 'release/v0.2.10-final/win-unpacked/resources/characters'
rows = json.loads((root / 'test-results/particle-renderer031.json').read_text('utf8'))
expected = {Path(row['character']) / row['model'] for row in rows}

def digest(file):
    with file.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

files = sorted(file.relative_to(current) for file in current.rglob('*') if file.is_file())
assert set(files) == {file.relative_to(packaged) for file in packaged.rglob('*') if file.is_file()}
changed, unchanged = [], []
for relative in files:
    assert digest(current / relative) == digest(packaged / relative), relative
    assert (previous / relative).is_file(), relative
    (changed if digest(current / relative) != digest(previous / relative) else unchanged).append(relative)
assert set(changed) == expected, changed
for relative in changed:
    old, old_binary = load(previous / relative)
    new, new_binary = load(current / relative)
    assert old_binary == new_binary, relative
    for material in new['materials']:
        spec = material.get('extras', {}).get('BA_cafeParticle')
        if spec:
            for key in ['m_ApplyActiveColorSpace', 'm_VertexStreams', 'm_UseCustomVertexStreams']:
                spec['renderer'].pop(key, None)
    assert old == new, relative

report = {
    'packagedAssetsIdenticalToSource': len(files),
    'changedModels': [str(file) for file in changed],
    'unchangedModels': sum(file.suffix == '.glb' for file in unchanged),
    'unchangedOtherFiles': sum(file.suffix != '.glb' for file in unchanged),
    'onlyRendererMetadataChanged': len(changed),
    'geometryTexturesAnimationBinaryPreserved': True,
}
(root / 'test-results/release031-scope.json').write_text(json.dumps(report, indent=2), 'utf8')
print(json.dumps(report, indent=2))
