"""Snapshot the user's model index and compare every in-scope entry explicitly."""
import json, pathlib, re, urllib.parse
from html.parser import HTMLParser
R=pathlib.Path(__file__).resolve().parents[1]
class Index(HTMLParser):
    def __init__(self): super().__init__(); self.heading=''; self.rows=[]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='h2':self.heading=a.get('id','')
        if a.get('class')=='model-viewer' and 'data-models' in a:
            self.rows.append({'character':self.heading,'models':json.loads(a['data-models'])})
p=Index();p.feed((R/'.assets/wiki-models-2026-10-23.html').read_text(encoding='utf8'))
installed=[json.loads(x.read_text(encoding='utf8')) for x in (R/'characters').glob('*/character.json')]
names={c['name'].split(' · ')[0] for c in installed}|{'优香','八云','未花','千世','绮良','忧'}
aliases={'绮罗罗':'绮良','日富美':'日富美','桃井':'小桃','绿':'小绿','桃':'小桃','凯':'凯伊','柯伊':'凯伊','伊织':'依织','白子＊恐怖':'白子','时':'时','淳子':'纯子'}
rows=[]
for row in p.rows:
    name=aliases.get(row['character'],row['character'])
    if name not in names:continue
    rows.append({**row,'localCharacter':name,'installed':[{'id':c['id'],'name':c['name']} for c in installed if c['name'].split(' · ')[0]==name]})
(R/'.assets/wiki-model-index-2026-10-23.json').write_text(json.dumps(p.rows,ensure_ascii=False,indent=2),encoding='utf8')
(R/'test-results/wiki-model-scope.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf8')
for row in rows:
    print(row['character'], ' | '.join(urllib.parse.unquote(x['src'].rsplit('/',1)[1]) for x in row['models']))
print('All headings:',', '.join(x['character'] for x in p.rows))
