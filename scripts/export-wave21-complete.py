"""Export own body animations for all 16 Wave 21 outfits via AssetRipperExporter."""
import json, os, re, subprocess, pathlib, UnityPy, sys

R = pathlib.Path(__file__).resolve().parents[1]
W = R / '.assets'
specs = json.loads((R / 'scripts/roster-wave21.json').read_text(encoding='utf8'))
if sys.argv[1:]:
    specs = {k: v for k, v in specs.items() if k in sys.argv[1:]}
profiles = json.loads((R / 'scripts/wave21-profiles.json').read_text('utf8'))

bindings = {}
excluded = {}
target_bundles = set()

for key, (prefix, _) in specs.items():
    files = [p for p in (W / 'selected').glob('*.bundle') if prefix.lower() + '-' in p.name and 'audio' not in p.name]
    env = UnityPy.load(*map(str, files))
    names = sorted({o.read().m_Name for o in env.objects if o.type.name == 'AnimationClip' and o.read().m_Name.startswith(prefix + '_')})
    skip = lambda n: bool(re.search(r'(?:_Cam(?:$|_)|_Dron|_prop|_Soldier|_my_)', n, re.I))
    bindings[prefix] = [n for n in names if not skip(n)]
    bindings[profiles[key]['modelPrefix']] = bindings[prefix]
    excluded[prefix] = [n for n in names if skip(n)]
    targets = [p for p in files if f'character-{prefix.lower()}-' in p.name and '-prefabs-' in p.name]
    assert targets, key
    for p in targets:
        target_bundles.add(p.name)

inputs = [
    {'path': str(p), 'node_id': p.name, 'target': p.name in target_bundles}
    for p in sorted((W / 'selected').glob('*.bundle'))
    if p.name in target_bundles or (
        'audio' not in p.name
        and any(k in p.name for k in ['-materials-', '-textures-', '-meshes-', '-animationclips-', '-animatorcontrollers-', '-assets-', '-prefabs-'])
        and not p.name.startswith('cafe-furniture-')
    )
]

request = {
    'schema_version': 0,
    'operation': 'export_primary_content',
    'inputs': inputs,
    'output_directory': str(W / 'exported/wave21-complete'),
    'concurrency': 2,
}
req = W / 'wave21-complete-request.json'
req.write_text(json.dumps(request), encoding='utf8')
bind = W / 'wave21-complete-bindings.json'
bind.write_text(json.dumps(bindings), encoding='utf8')
scope_path = R / 'test-results/wave21-body-clip-scope.json'
scope_path.write_text(json.dumps({'included': bindings, 'sceneOrCameraTracks': excluded}, indent=2), encoding='utf8')

print(f'Exporting {len(target_bundles)} target prefab bundles ({len(inputs)} total inputs)...', flush=True)
with (W / 'wave21-complete-export.log').open('w', encoding='utf8') as log:
    result = subprocess.run(
        [str(R / '.cache/dotnet/dotnet.exe'), str(W / 'euler-exporter/AssetRipperExporter.dll'), str(req), str(W / 'wave21-complete-result.json')],
        env={**os.environ, 'BA_FURNITURE_BINDINGS': str(bind), 'BA_COMPLETE_PATH_CACHE': '1'},
        stdout=log,
        stderr=subprocess.STDOUT,
    )
assert result.returncode == 0, f'Exporter failed with code {result.returncode}'
print('Exported own body clips for', len(specs), 'outfits', flush=True)
