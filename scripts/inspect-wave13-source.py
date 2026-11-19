"""Record the native role roots, face defaults and clip names before adaptation."""
import json
from pathlib import Path
import UnityPy
R=Path(__file__).resolve().parents[1];specs=json.loads((R/'scripts/roster-wave13.json').read_text('utf8'));rows={}
for key,(prefix,_) in specs.items():
 files=[p for p in (R/'.assets/selected').glob('*.bundle')if prefix.lower()+'-'in p.name]
 env=UnityPy.load(*map(str,files));row={'roots':[],'faceDefaults':[],'clips':[]}
 for o in env.objects:
  if o.type.name=='GameObject':
   go=o.read();t=next((c.component.read()for c in go.m_Component if c.component.deref().type.name=='Transform'),None)
   if t and not t.m_Father.m_PathID:row['roots'].append(go.m_Name)
  if o.type.name=='MonoBehaviour':
   d=o.read_typetree()
   if'MouthDefaultUV'in d:row['faceDefaults'].append({'root':o.read().m_GameObject.read().m_Name,'default':d['MouthDefaultUV'],'fields':{k:v for k,v in d.items()if 'Mouth'in k or 'Renderer'in k}})
  if o.type.name=='AnimationClip':row['clips'].append(o.read().m_Name)
 rows[key]=row
(R/'test-results/wave13-original-structure.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),'utf8')
print(json.dumps(rows,ensure_ascii=False,indent=2))
