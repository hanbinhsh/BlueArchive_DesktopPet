"""Resolve original prefabs, authored basic clips and halo availability before adapting."""
from pathlib import Path
import json,UnityPy
R=Path(__file__).resolve().parents[1];W=R/'.assets';specs=json.loads((R/'scripts/roster-wave15.json').read_text('utf8'));rows={};profiles={}
choices=[('idle','待机','Cafe_Idle'),('interact','咖啡厅互动','Cafe_Reaction'),('walk','原地走路','Cafe_Walk'),('victory','胜利动作','Victory_Start'),('reload','换弹','Normal_Reload'),('pickup','编队提起','Formation_Pickup')]
for key,(prefix,_) in specs.items():
 files=[p for p in (W/'selected').glob('*.bundle')if prefix.lower()+'-'in p.name];env=UnityPy.load(*map(str,files));row={'roots':[],'faceDefaults':[],'clips':[],'haloParents':[]}
 for o in env.objects:
  if o.type.name=='GameObject':
   go=o.read();t=next((c.component.read()for c in go.m_Component if c.component.deref().type.name=='Transform'),None)
   if t and not t.m_Father.m_PathID:row['roots'].append(go.m_Name)
  elif o.type.name=='MonoBehaviour':
   d=o.read_typetree();native=o.read()
   if not native.m_GameObject.m_PathID:continue
   go=native.m_GameObject.read()
   if'MouthDefaultUV'in d:row['faceDefaults'].append({'root':go.m_Name,'default':d['MouthDefaultUV'],'fields':{k:v for k,v in d.items()if'Mouth'in k or'Renderer'in k}})
   if'FollowTarget'in d and'TargetRelativePosition'in d:
    t=next(c.component.read()for c in go.m_Component if c.component.deref().type.name=='Transform')
    if t.m_Father.m_PathID:row['haloParents'].append(t.m_Father.read().m_GameObject.read().m_Name)
  elif o.type.name=='AnimationClip':row['clips'].append(o.read().m_Name)
 roots={x['root']for x in row['faceDefaults']};model=next((n for n in [prefix,'Cafe_'+prefix,prefix+'_CafeOnly']if n in roots),None);assert model,(key,roots)
 actions=[]
 for a,b,suffix in choices:
  variants=[prefix+'_'+suffix]
  if a=='pickup':variants.append(prefix+'_Fomation_Pickup')
  clip=next((v for v in variants if v in row['clips']),None)
  if clip:actions.append([a,b,clip])
 assert {'idle','interact'}<={a[0]for a in actions},key
 profile={'modelPrefix':model,'prefabName':model,'exportDirectory':'wave15-complete','actions':actions}
 native=next(x for x in row['faceDefaults']if x['root']==model)
 if not native['fields']['MouthRenderer']['m_PathID']:
  assert native['fields']['MouthMaterialIndex']==-1;profile['noMouthAtlas']=True
 if model not in row['haloParents']:profile['noHalo']=True
 profiles[key]=profile;rows[key]=row;print(key,model,'basic',len(actions),'halo',not profile.get('noHalo',False),flush=True)
(R/'test-results/wave15-original-structure.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),'utf8');(R/'scripts/wave15-profiles.json').write_text(json.dumps(profiles,ensure_ascii=False,indent=2),'utf8')
