"""Export all 11 Field-Cafe standalone furniture prefabs and 3 Field-Player character clip rigs (hina, hina_dress, seia)."""
import json, os, subprocess, pathlib

R = pathlib.Path(__file__).resolve().parents[1]
W = R / '.assets'

rows = json.loads((W / 'field-cafe-timelines.json').read_text('utf8'))

bindings = {}
# Map character field clips onto Field_Player_*_NonWeapon prefabs
CHAR_PREFABS = {
    'hina': 'Field_Player_Hina_Original_NonWeapon',
    'hina_dress': 'Field_Player_CH0230_NonWeapon',
    'seia': 'Field_Player_CH0070_NonWeapon',
}

for r in rows:
    prefab = r['prefab']
    char_prefab = CHAR_PREFABS.get(r['character'])
    for t in r['tracks']:
        for c in t['clips']:
            if c['type'] != 'AnimationPlayableAsset':
                continue
            nm = c['name']
            if nm.startswith('Field_Player_'):
                if char_prefab:
                    bindings.setdefault(char_prefab, set()).add(nm)
            else:
                # Bind to both prefab root and its Animator child (*_Mesh or explicit binding)
                bindings.setdefault(prefab, set()).add(nm)
                bindings.setdefault(prefab + '_Mesh', set()).add(nm)
                if t.get('binding'):
                    bindings.setdefault(t['binding'].split('/')[-1], set()).add(nm)

bindings_json = {k: sorted(v) for k, v in bindings.items()}
bind_path = W / 'field-cafe-bindings.json'
bind_path.write_text(json.dumps(bindings_json, indent=2, ensure_ascii=False), encoding='utf8')

target_bundles = {
    'field-cafe-_mxload-prefabs-2025-07-02_assets_all_9108106.bundle',
    'field-cafe-_mxload-prefabs-2026-04-27_assets_all_1871240492.bundle',
    'field-character-_mxload-prefabs-2025-07-02_assets_all_2148108625.bundle',
}

inputs = [
    {'path': str(p), 'node_id': p.name, 'target': p.name in target_bundles}
    for p in sorted((W / 'selected').glob('*.bundle'))
    if p.name in target_bundles or (
        'audio' not in p.name
        and any(k in p.name for k in ['-materials-', '-textures-', '-meshes-', '-animationclips-', '-animatorcontrollers-', '-assets-', '-prefabs-'])
        and not p.name.startswith('cafe-furniture-')
    )
]

out_dir = W / 'field-cafe-exported'
request = {
    'schema_version': 0,
    'operation': 'export_primary_content',
    'inputs': inputs,
    'output_directory': str(out_dir),
    'concurrency': 2,
}
req_path = W / 'field-cafe-export-request.json'
req_path.write_text(json.dumps(request), encoding='utf8')

print(f'Exporting {len(target_bundles)} Field-Cafe target bundles ({len(inputs)} total inputs)...', flush=True)
with (W / 'field-cafe-export.log').open('w', encoding='utf8') as log:
    result = subprocess.run(
        [str(R / '.cache/dotnet/dotnet.exe'), str(W / 'euler-exporter/AssetRipperExporter.dll'), str(req_path), str(W / 'field-cafe-export-result.json')],
        env={**os.environ, 'BA_FURNITURE_BINDINGS': str(bind_path), 'BA_COMPLETE_PATH_CACHE': '1'},
        stdout=log,
        stderr=subprocess.STDOUT,
    )
assert result.returncode == 0, f'Exporter failed with code {result.returncode}'
print('Exported Field-Cafe prefabs and character clips to', out_dir, flush=True)
