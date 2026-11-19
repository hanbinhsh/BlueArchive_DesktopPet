from pathlib import Path
import json,UnityPy
files=[p for p in Path('.assets/selected').glob('*.bundle')if'characters-ch0304-'in p.name];env=UnityPy.load(*map(str,files));rows=[]
def shape(v,depth=0):
 if isinstance(v,dict):return {k:shape(x,depth+1)for k,x in v.items()if depth<5 or not isinstance(x,(dict,list))}
 if isinstance(v,list):return dict(length=len(v),first=[shape(x,depth+1)for x in v[:2]])
 return v
for o in env.objects:
 if o.type.name!='AnimationClip':continue
 d=o.read_typetree()
 if d.get('m_Name')in ['CH0304_Cafe_Idle','CH0304_Normal_Reload','CH0304_Formation_Pickup','CH0304_Normal_Idle']:
  rows.append(dict(name=d['m_Name'],cab=o.assets_file.name,fields=shape(d),raw=d))
Path('test-results/eri15-native-clip-inspection.json').write_text(json.dumps(rows),'utf8')
for r in rows:print(r['name'],r['cab'],json.dumps(r['fields'])[:7500])
