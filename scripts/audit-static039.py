"""Compare every installed furniture surface with its cached original shader."""
from pathlib import Path
from collections import defaultdict
import json,UnityPy
from glb import load
from source_dependencies import resolve_cached

env=UnityPy.load(*map(str,Path('.assets/selected').glob('*cafe*materials*.bundle')))
originals={o.read().m_Name:o.read()for o in list(env.objects)if o.type.name=='Material'}
rows=[];errors=[];seen=set()
for cp in Path('characters').glob('*/character.json'):
 for f in json.loads(cp.read_text('utf8')).get('furniture',[]):
  key=(cp.parent.name,f['model'])
  if key in seen:continue
  seen.add(key);d,b=load(cp.parent/f['model'])
  for i,m in enumerate(d['materials']):
   if m.get('extras',{}).get('BA_cafeParticle'):continue
   original=originals.get(m.get('name'))
   if original is None:continue
   try:shader=resolve_cached(env,original.m_Shader.read).m_ParsedForm.m_Name
   except(KeyError,FileNotFoundError)as error:errors.append(dict(character=key[0],model=key[1],material=m['name'],error=str(error)));continue
   props=dict(original.m_SavedProperties.m_Colors);tint=props.get('_Tint')
   row=dict(character=key[0],model=key[1],material=m['name'],index=i,shader=shader,alpha=m.get('alphaMode','OPAQUE'),extras=list(m.get('extras',{})),baseColor=m.get('pbrMetallicRoughness',{}).get('baseColorFactor',[1,1,1,1]))
   if tint:row['nativeTint']=[getattr(tint,k)for k in 'rgba']
   if shader.startswith('DSFX/')and not any(k in m.get('extras',{})for k in ['BA_smokeFx','BA_waterFx','BA_sourceShader']):row['unadaptedDSFX']=True
   if shader in ['MX/C-Simple','MX/C-Simple-Transparent']and tint and any(abs(a-max(0,min(1,b)))>1e-5 for a,b in zip(row['baseColor'],row['nativeTint'])):row['tintMismatch']=True
   rows.append(row)
report=dict(models=len(seen),materials=len(rows),errors=errors,rows=rows)
Path('test-results/static039-source-audit.json').write_text(json.dumps(report,indent=2),'utf8')
for r in rows:
 if r.get('unadaptedDSFX')or r.get('tintMismatch'):print(r)
print('Models',len(seen),'materials',len(rows),'source errors',len(errors))
