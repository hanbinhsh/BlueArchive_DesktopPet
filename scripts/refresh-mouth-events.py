"""Preserve all supported mouth events in installed original character packs."""
import json
from pathlib import Path
from glb import load
from mouth_events import mouth_events

changed = []
for path in Path('characters').glob('*/character.json'):
    manifest = json.loads(path.read_text('utf-8'))
    if 'mouth' not in manifest: continue
    doc, _ = load(path.parent/manifest['model'])
    clips = {c['track']:c for c in doc['scenes'][0]['extras']['BAAD_unity_animation']['clips']}
    events = {name:mouth_events(clips[name],manifest['mouth']['defaultTile']) for name in manifest['mouth']['events']}
    if events == manifest['mouth']['events']: continue
    manifest['mouth']['events'] = events
    path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n','utf-8')
    changed.append(manifest['id'])
Path('test-results/mouth-events-updated.json').write_text(json.dumps(changed,indent=2))
print('Updated original mouth events:',changed)
