"""Append Wave 20 outfits to the verified furniture index and list their furniture interactions."""
import json, shutil
from pathlib import Path

R = Path(__file__).resolve().parents[1]
W = R / '.assets'
backup = W / 'pre-wave20'
backup.mkdir(exist_ok=True)
for name in ['furniture-index.json', 'furniture-profiles.json', 'furniture-bindings.json', 'furniture-timelines.json']:
    if not (backup / name).exists():
        shutil.copy2(W / name, backup / name)

def read(p): return json.loads(p.read_text('utf8'))

specs = read(R / 'scripts/roster-wave20.json')
data = read(W / 'students-wave16-en.json')
furniture = read(W / 'furniture-wave16-cn.json')
idx = read(W / 'furniture-index.json')
entries = {f"{x['character']}:{x['furnitureId']}:{x['variant']}": x for x in idx['entries']}
new = []
missing_prefabs = []
for s in data.values():
    if s['PathName'] not in specs:
        continue
    for fid, variant in s.get('FurnitureInteraction', [[]])[0]:
        f = furniture[str(fid)]
        icon = 'my_event083_beachsunbed' if (s['PathName'] == 'misaki_swimsuit' and fid == 17105) else f['Icon']
        row = dict(character=s['PathName'], studentId=s['Id'], devName=s['DevName'], furnitureId=fid, variant=variant, name=f['Name'], icon=icon)
        if row['icon'].lower() not in idx['prefabs']:
            missing_prefabs.append(row)
            continue
        entries[f"{row['character']}:{fid}:{variant}"] = row
        new.append(row)

idx['entries'] = list(entries.values())
(W / 'furniture-index.json').write_text(json.dumps(idx, ensure_ascii=False, indent=2), 'utf8')
(R / 'test-results/wave20-furniture-index.json').write_text(json.dumps(new, ensure_ascii=False, indent=2), 'utf8')
print(f'Indexed {len(new)} furniture interactions for Wave 20 (missing prefabs: {len(missing_prefabs)}):')
for r in new:
    print(f"  {r['character']:20s} f{r['furnitureId']} ({r['icon']}) -> {r['name']}")
if missing_prefabs:
    print('MISSING PREFABS:', missing_prefabs)
