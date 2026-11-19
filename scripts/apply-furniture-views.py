"""Apply reviewed scene view angles, in units of pi, without rebaking geometry."""
import json,math,pathlib
root=pathlib.Path(__file__).resolve().parents[1]
views=json.loads((root/'scripts/furniture-view-yaw.json').read_text())
count=0
for file in (root/'characters').glob('*/character.json'):
    c=json.loads(file.read_text(encoding='utf8'))
    if not c.get('furniture'):continue
    for f in c['furniture']:
        f['yaw']=math.pi*views[f['id'].split('_')[0][1:]];count+=1
    file.write_text(json.dumps(c,indent=2,ensure_ascii=False),encoding='utf8')
print('Reviewed furniture views',count)
