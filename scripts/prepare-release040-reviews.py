from pathlib import Path
import json,shutil
R=Path(__file__).resolve().parents[1];T=R/'test-results';ids=json.loads((R/'scripts/roster-wave14.json').read_text('utf8'))
rows=[dict(character=k,id=f['id'],status='ready')for k in ids for f in json.loads((R/'characters'/k/'character.json').read_text('utf8')).get('furniture',[])]
(T/'final040-rows.json').write_text(json.dumps(rows,indent=2),'utf8')
cases=[]
for row in rows:
 c=json.loads((R/'characters'/row['character']/'character.json').read_text('utf8'));f=next(f for f in c['furniture']if f['id']==row['id'])
 cases.append(dict(character=row['character'],steps=[dict(kind='furniture',id=f['id'],mode='seconds',value=round(f['duration']+.25,3),gap=0)]))
for k in ['mashiro','shimiko']:
 cases.append(dict(character=k,steps=[dict(kind='action',id='interact',mode='seconds',value=12,gap=0)]))
for k,f in [('tsurugi_swimsuit','f4400_0'),('eimi_swimsuit','f210324_0'),('mine','f207310_0')]:
 c=json.loads((R/'characters'/k/'character.json').read_text('utf8'));found=next((x for x in c['furniture']if x['id']==f),c['furniture'][0]);cases.append(dict(character=k,steps=[dict(kind='furniture',id=found['id'],mode='seconds',value=30,gap=0)]))
(T/'release040-soak-cases.json').write_text(json.dumps(cases,indent=2),'utf8')
p=(R/'scripts/release034-soak.mjs').read_text('utf8').replace("cycleStart<100000","cycleStart<180000")
(R/'scripts/release040-soak.mjs').write_text(p,'utf8')
