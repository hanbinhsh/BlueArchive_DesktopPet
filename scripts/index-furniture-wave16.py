"""Append only the requested new outfits to the existing verified furniture index."""
import json,shutil
from pathlib import Path
R=Path(__file__).resolve().parents[1];W=R/'.assets';backup=W/'pre-wave16';backup.mkdir(exist_ok=True)
for name in ['furniture-index.json','furniture-profiles.json','furniture-bindings.json','furniture-timelines.json']:
 if not (backup/name).exists():shutil.copy2(W/name,backup/name)
def read(p):return json.loads(p.read_text('utf8'))
specs=read(R/'scripts/roster-wave16.json');data=read(W/'students-wave16-en.json');furniture=read(W/'furniture-wave16-cn.json');idx=read(W/'furniture-index.json')
entries={f"{x['character']}:{x['furnitureId']}:{x['variant']}":x for x in idx['entries']}
new=[]
for s in data.values():
 if s['PathName'] not in specs:continue
 for fid,variant in s.get('FurnitureInteraction',[[]])[0]:
  f=furniture[str(fid)];row=dict(character=s['PathName'],studentId=s['Id'],devName=s['DevName'],furnitureId=fid,variant=variant,name=f['Name'],icon=f['Icon'])
  assert row['icon'].lower() in idx['prefabs'],row
  entries[f"{row['character']}:{fid}:{variant}"]=row;new.append(row)
idx['entries']=list(entries.values());(W/'furniture-index.json').write_text(json.dumps(idx,ensure_ascii=False,indent=2),'utf8')
(R/'test-results/wave16-furniture-index.json').write_text(json.dumps(new,ensure_ascii=False,indent=2),'utf8')
print(json.dumps(new,ensure_ascii=False,indent=2))
