"""Prepare this batch's isolated scripts without altering previous release assets."""
from pathlib import Path
import json,re
R=Path(__file__).resolve().parents[1];S=R/'scripts'
p=S/'roster-wave14.json';specs=json.loads(p.read_text('utf8'))
for key,value in specs.items():
 label=value[1];match=re.fullmatch(r'(.+?)[（(](.+)[）)]',label)
 if match:value[1]=match[1]+' · '+match[2]
 elif' · 'not in label:value[1]=label+' · 原版'
p.write_text(json.dumps(specs,ensure_ascii=False,indent=2),'utf8')
for old,new in [('prepare-wave13.py','prepare-wave14.py'),('export-wave13-complete.py','export-wave14-complete.py'),('index-wave13-sources.py','index-wave14-sources.py'),('index-furniture-wave13.py','index-furniture-wave14.py'),('merge-furniture-wave13.py','merge-furniture-wave14.py')]:
 text=(S/old).read_text('utf8').replace('wave13','wave14')
 if old=='export-wave13-complete.py':text=text.replace("    if key=='wakamo':bindings['Cafe_Wakamo_Original']=bindings[prefix]\n",'')
 if old=='merge-furniture-wave13.py':text=text.replace("|{'iroha_swimsuit'}",'')
 (S/new).write_text(text,'utf8')
