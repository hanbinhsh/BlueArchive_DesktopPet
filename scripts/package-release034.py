"""Package the verified 0.2.14 build without changing previous releases."""
from pathlib import Path
import hashlib
import json
import zipfile

root = Path(__file__).resolve().parent.parent
base = root / 'release/v0.2.14/win-unpacked'
out = root / 'release/BA-Desktop-Pet-0.2.14-win-x64.zip'
source = root / 'release/BA-Desktop-Pet-0.2.14-source.zip'

soak = json.loads((root / 'test-results/release034-soak.json').read_text('utf8'))
assert soak['complete'] and soak['version']=='0.2.14' and soak['elapsedSeconds']>=1800 and not soak['errors']
inventory = json.loads((root / 'test-results/particle-renderer034.json').read_text('utf8'))

# Refresh only documentation after the completed regression; the tested executable
# and model resources remain untouched.
package = json.loads((root / 'package.json').read_text('utf8'))
assert package['version'] == '0.2.14'
for item in package['build']['extraFiles']:
    target = base / item['to']
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes((root / item['from']).read_bytes())

def digest(file):
    with file.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

for item in inventory:
    model = base / 'resources/characters' / item['character'] / item['model']
    assert digest(model) == item['sha256'], model
# Check every packaged character resource, not only the three edited GLBs.
for file in (root / 'characters').rglob('*'):
    if file.is_file():
        target = base / 'resources/characters' / file.relative_to(root / 'characters')
        assert digest(file) == digest(target), target
verification = json.loads((root / 'test-results/release034-verification.json').read_text('utf8'))
assert digest(base / 'resources/app.asar') == verification['appAsarSha256']

with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
    for file in sorted(base.rglob('*')):
        if file.is_file():
            archive.write(file, file.relative_to(base))
with zipfile.ZipFile(out) as archive:
    assert archive.testzip() is None
    for name in archive.namelist():
        with archive.open(name) as stream:
            assert hashlib.file_digest(stream, 'sha256').hexdigest() == digest(base / name), name
    count = len(archive.namelist())

with zipfile.ZipFile(source, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
    for folder in ['src', 'scripts', 'tests', 'docs', 'native']:
        for file in sorted((root / folder).rglob('*')):
            if file.is_file() and '__pycache__' not in file.parts and 'bin' not in file.parts:
                archive.write(file, file.relative_to(root))
    for name in ['package.json', 'package-lock.json', 'tsconfig.json', 'README.md']:
        archive.write(root / name, name)
    for name in [
        'particle-renderer034.json', 'fx034-sweep-runtime.json',
        'release034-soak.json', 'unit034.log', 'typecheck034.log',
        'assets034.log', 'release034-verification.json', 'release034-resources.json',
        'full034-adaptation.json', 'fx034-affected.json', 'fx034-source-audit.json',
        'stretch034-affected.json', 'bubbles034-preview.json', 'bubbles034-runtime.json',
        'release034-speed.json', 'emission034.log', 'ui034-before-contact.jpg',
        'ui034-after-contact.jpg', 'ui034-sigh-before.jpg',
    ] + [f'fx034-contact-{i:02}.jpg' for i in range(7)] + [f'bubbles034-contact-{i:02}.jpg' for i in range(4)]:
        archive.write(root / 'test-results' / name, 'validation/' + name)
    archive.writestr('SOURCE-SETUP.md',
        'Run npm ci, copy resources/characters from the portable package into characters/, '
        'then npm run build. The Windows wheel helper is included in the portable '
        'package at resources/native/wheel-forwarder.exe; copy it to '
        'native/bin/wheel-forwarder.exe to build a portable package. '
        'Acquisition caches and game model files are not included in this source ZIP. '
        'See docs/AUDIT-034.md for validation and rendering limitations.\n')
with zipfile.ZipFile(source) as archive:
    assert archive.testzip() is None

report = {
    'portable': {'path': str(out), 'bytes': out.stat().st_size,
                 'files': count, 'sha256': digest(out)},
    'source': {'path': str(source), 'bytes': source.stat().st_size,
               'sha256': digest(source)},
}
(root / 'test-results/release034.json').write_text(json.dumps(report, indent=2), 'utf8')
print(json.dumps(report, indent=2))
