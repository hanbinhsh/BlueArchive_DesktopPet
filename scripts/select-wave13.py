"""Snapshot current data and the user's model index for Wakamo and Ibuki."""
from pathlib import Path
from html.parser import HTMLParser
import json,hashlib,httpx
R=Path(__file__).resolve().parents[1];W=R/'.assets'
def fetch(url,path):
 response=httpx.get(url,timeout=90,follow_redirects=True);response.raise_for_status();path.write_bytes(response.content)
 return {'url':url,'sha256':hashlib.sha256(response.content).hexdigest()}
sources={lang:fetch(f'https://schaledb.com/data/{lang}/students.json',W/f'students-wave13-{lang}.json')for lang in ['en','cn']}
data=json.loads((W/'students-wave13-en.json').read_text('utf8'))
selected=[{k:s.get(k)for k in ['Id','Name','PersonalName','DevName','PathName','IsReleased']}for s in data.values()if s['PersonalName']in ['Wakamo','Ibuki']and s['IsReleased'][0]]
class Index(HTMLParser):
 def __init__(self):super().__init__();self.heading='';self.rows=[]
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if tag=='h2':self.heading=a.get('id','')
  if a.get('class')=='model-viewer'and'data-models'in a and self.heading in ['若藻','伊吹']:self.rows.append({'character':self.heading,'models':json.loads(a['data-models'])})
sources['wiki']=fetch('https://zh.bluearchive.wiki/wiki/%E8%A7%92%E8%89%B2%E6%A8%A1%E5%9E%8B',W/'wiki-wave13.html')
p=Index();p.feed((W/'wiki-wave13.html').read_text('utf8'))
result={'date':'2026-11-17','requested':['Wakamo','Ibuki'],'sources':sources,'students':selected,'wiki':p.rows}
(R/'test-results/wave13-selection.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),'utf8')
print(json.dumps({'students':selected,'wiki':p.rows},ensure_ascii=False,indent=2))
