"""Inventory named scene dependencies without mistaking them for complete scenes."""
import json,re
from pathlib import Path
R=Path(__file__).resolve().parents[1];rows=[]
for p in (R/'characters').glob('*/character.json'):
    c=json.loads(p.read_text(encoding='utf8'))
    for a in c['actions']:
        if re.search(r'Cafe_Prop|Cafe_Interact|TSS_Interact|NonWeapon|Furniture|Bed|Sofa|Chair|Piano|Drum|DessertTable|Study|(?:^|_)(?:Sit|Sleep|Desk|Table|Field|Scenario)(?:_|$)',a['clip'].split('--')[0],re.I):
            rows.append({'character':c['id'],'name':c['name'],'action':a['id'],'clip':a['clip'],'furniture':[f['id'] for f in c.get('furniture',[])]})
(R/'test-results/scene-action-candidates.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf8')
for r in rows:print(r['character'],r['action'],r['clip'])
print('Candidates:',len(rows))
