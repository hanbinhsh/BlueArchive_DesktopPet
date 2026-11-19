"""Choose five distinct, not-yet-installed student groups, without rerolling."""
import json,random,secrets,hashlib
from pathlib import Path
import httpx
R=Path(__file__).resolve().parents[1];W=R/'.assets'
def read(p):return json.loads(p.read_text(encoding='utf8'))
out=R/'test-results/wave9-selection.json'
if out.exists():
    print(out.read_text(encoding='utf8'));raise SystemExit
snapshots={}
for lang in ['en','cn']:
    url=f'https://schaledb.com/data/{lang}/students.json'
    response=httpx.get(url,timeout=60,follow_redirects=True);response.raise_for_status()
    p=W/f'students-wave9-{lang}-2026-10-24.json';p.write_bytes(response.content)
    snapshots[lang]={'url':url,'sha256':hashlib.sha256(response.content).hexdigest(),'data':response.json()}
students=snapshots['en']['data'];chinese=snapshots['cn']['data']
installed={r['sourceName'] for r in read(R/'test-results/costume-coverage.json')['characters']}
groups={}
for key,s in students.items():
    if s['IsReleased'][0]:groups.setdefault(s['PersonalName'],[]).append(s)
assert 'Miku' in groups
pool=sorted(set(groups)-installed-{'Miku'})
seed=secrets.randbits(64);selected=random.Random(seed).sample(pool,5)
report={'date':'2026-10-24','seed':seed,'pool':pool,'selected':selected,'requested':['Miku'],'sources':{k:{a:b for a,b in v.items() if a!='data'} for k,v in snapshots.items()},'characters':[]}
for name in ['Miku']+selected:
    rows=[]
    for s in groups[name]:
        cn=chinese[str(s['Id'])]
        rows.append({'id':s['Id'],'name':s['Name'],'chineseName':cn['Name'],'path':s['PathName'],'devName':s['DevName'],'personalName':name})
    report['characters'].append({'name':name,'outfits':rows})
out.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({k:report[k] for k in ['seed','selected','characters']},ensure_ascii=False,indent=2))
