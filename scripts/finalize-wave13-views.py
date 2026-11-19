"""Install the front three-quarter angles chosen from the four-view comparison."""
import json,math
from pathlib import Path
R=Path(__file__).resolve().parents[1];specs=json.loads((R/'scripts/roster-wave13.json').read_text('utf8'));p=R/'scripts/furniture-character-view-yaw.json';settings=json.loads(p.read_text('utf8'));rows=[]
for key in specs:
 path=R/'.assets/expanded-ready'/key/'character.json';c=json.loads(path.read_text('utf8'))
 for f in c.get('furniture',[]):
  f['yaw']=math.pi/4;settings.setdefault(key,{})[f['id']]=.25;rows.append(dict(character=key,id=f['id'],yaw=f['yaw']))
 path.write_text(json.dumps(c,ensure_ascii=False,indent=2),'utf8')
p.write_text(json.dumps(settings,ensure_ascii=False,indent=2),'utf8')
(R/'test-results/wave13-view-selection.json').write_text(json.dumps(rows,indent=2),'utf8')
