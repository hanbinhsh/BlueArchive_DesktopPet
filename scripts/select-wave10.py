"""Draw five distinct student groups once, retaining seed and current source snapshot."""
import json,random,secrets,hashlib
from pathlib import Path
import httpx
R=Path(__file__).resolve().parents[1];W=R/'.assets';out=R/'test-results/wave10-selection.json'
if out.exists():print(out.read_text(encoding='utf8'));raise SystemExit
def read(p):return json.loads(p.read_text(encoding='utf8'))
installed={x['sourceName'] for x in read(R/'test-results/costume-coverage.json')['characters']}
last=read(R/'test-results/wave9-selection.json');installed.update(last['selected']+last['requested'])
sources={};data={}
for lang in ['en','cn']:
 url=f'https://schaledb.com/data/{lang}/students.json';response=httpx.get(url,timeout=60,follow_redirects=True);response.raise_for_status()
 (W/f'students-wave10-{lang}.json').write_bytes(response.content);data[lang]=response.json();sources[lang]={'url':url,'sha256':hashlib.sha256(response.content).hexdigest()}
groups={}
for s in data['en'].values():
 if s['IsReleased'][0]:groups.setdefault(s['PersonalName'],[]).append(s)
pool=sorted(set(groups)-installed);seed=secrets.randbits(64);selected=random.Random(seed).sample(pool,5)
result={'seed':seed,'installed':sorted(installed),'pool':pool,'selected':selected,'sources':sources,'characters':[]}
for name in selected:
 result['characters'].append({'name':name,'outfits':[{'id':s['Id'],'name':s['Name'],'chineseName':data['cn'][str(s['Id'])]['Name'],'path':s['PathName'],'devName':s['DevName']} for s in groups[name]]})
out.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(result['characters'],ensure_ascii=False,indent=2))
