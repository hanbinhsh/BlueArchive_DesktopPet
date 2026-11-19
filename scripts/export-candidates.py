"""Run the pinned asset-downloader GLB exporter on verified candidate bundles."""
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
work = ROOT / '.assets'
for character, key in ([('serika_newyear', 'serika_newyear')] if '--newyear' in sys.argv else [('serika', 'serika_original'), ('plana', 'npcs-plana')]):
    files = sorted((work / 'selected').glob(f'*{key}*.bundle'))
    if not files:
        raise RuntimeError(f'Missing bundles: {character}')
    request = {
        'schema_version': 0,
        'operation': 'export_primary_content',
        'inputs': [{'path': str(p), 'node_id': p.name, 'target': True} for p in files],
        'output_directory': str(work / 'exported' / character),
        'concurrency': 2
    }
    request_path = work / f'{character}-request.json'
    request_path.write_text(json.dumps(request), encoding='utf-8')
    with (work / f'{character}-export.log').open('w', encoding='utf-8') as log:
        result = subprocess.run(['dotnet', str(work / 'exporter/AssetRipperExporter.dll'), str(request_path), str(work / f'{character}-result.json')], stdout=log, stderr=subprocess.STDOUT)
    print(character, 'export exit:', result.returncode, flush=True)
    if result.returncode:
        print((work / f'{character}-export.log').read_text(encoding='utf-8')[-4000:])
